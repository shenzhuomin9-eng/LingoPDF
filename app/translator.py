"""翻译引擎核心：封装 pdf2zh，统一三种翻译后端。

- openai : OpenAI 兼容 API（DeepSeek / GLM / OpenAI / 任意中转），质量最高
- google : Google 翻译免费网页接口，零配置但需联网
- argos  : Argos Translate 本地神经翻译模型，完全离线，轻量

排版保留由 pdf2zh 的版面检测 + PDF 重排引擎负责，与翻译后端无关，
因此三种引擎输出效果排版一致。
"""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ── 数据结构 ────────────────────────────────────────────


@dataclass
class TranslateOptions:
    """一次翻译任务的全部参数。"""

    engine: str = "openai"       # openai | google | argos
    base_url: str = ""
    api_key: str = ""
    model: str = "deepseek-chat"
    lang_in: str = "en"
    lang_out: str = "zh"
    dual: bool = False           # 额外输出双语对照版


@dataclass
class TranslateResult:
    """单个文件的翻译结果。"""

    files: list[dict] = field(default_factory=list)  # [{name, path}]
    elapsed: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


def normalize_base_url(url: str) -> str:
    """确保 base_url 以 /v1 结尾（OpenAI 兼容规范）。"""
    url = (url or "").strip().rstrip("/")
    if not url:
        return ""
    if not url.endswith("/v1"):
        url += "/v1"
    return url


# ── pdf2zh 导入补丁 ─────────────────────────────────────
# 必须在模块加载时就执行，否则 main.py 的 import 会先触发 pdf2zh 导入

_patched = False
_patch_lock = threading.Lock()


def _apply_tencentcloud_patch():
    """打 tencentcloud 补丁 + 注册离线 Argos 翻译器。"""
    global _patched
    if _patched:
        return
    with _patch_lock:
        if _patched:
            return
        try:
            import tencentcloud.tmt.v20180321.models as models
            for n in ("TextTranslateRequest", "TextTranslateResponse"):
                if not hasattr(models, n):
                    setattr(models, n, type(n, (), {"__init__": lambda self, *a, **k: None}))
        except Exception:
            pass

        # 离线优先的 Argos 翻译器
        try:
            from pdf2zh.translator import ArgosTranslator, BaseTranslator

            class OfflineArgosTranslator(ArgosTranslator):
                name = "argos"

                def __init__(self, lang_in, lang_out, model, ignore_cache=False, **kwargs):
                    BaseTranslator.__init__(self, lang_in, lang_out, model, ignore_cache)
                    import argostranslate.translate
                    codes = {l.code for l in argostranslate.translate.get_installed_languages()}
                    if self.lang_in not in codes or self.lang_out not in codes:
                        raise ValueError(
                            f"Argos 本地模型未安装: {self.lang_in}→{self.lang_out}，请先在设置中下载"
                        )

                def translate(self, text: str, ignore_cache: bool = False):
                    import argostranslate.translate
                    installed = argostranslate.translate.get_installed_languages()
                    from_lang = next(l for l in installed if l.code == self.lang_in)
                    to_lang = next(l for l in installed if l.code == self.lang_out)
                    return from_lang.get_translation(to_lang).translate(text)

            import pdf2zh.converter as _conv
            import pdf2zh.translator as _tr
            _conv.ArgosTranslator = OfflineArgosTranslator
            _tr.ArgosTranslator = OfflineArgosTranslator
            logger.debug("已注册离线优先的 ArgosTranslator")
        except Exception as e:
            logger.warning("Argos 离线补丁失败: %s", e)

        _patched = True


# 模块加载时立即执行补丁
_apply_tencentcloud_patch()


# ── ONNX 版面模型单例（避免每个任务重复加载）────────────


_onnx_model = None
_onnx_lock = threading.Lock()


def get_layout_model(on_log: Optional[Callable[[str], None]] = None):
    global _onnx_model
    with _onnx_lock:
        if _onnx_model is None:
            if on_log:
                on_log("加载版面检测模型（首次约 5-10 秒）...")
            from pdf2zh.doclayout import OnnxModel

            _onnx_model = OnnxModel.load_available()
            if on_log:
                on_log("版面模型加载完成")
        return _onnx_model


# ── 连通性测试 ──────────────────────────────────────────


def test_connection(opts: TranslateOptions) -> tuple[bool, str]:
    """测试翻译引擎是否可用，返回 (成功?, 消息)。"""
    if opts.engine == "openai":
        return _test_openai(opts)
    if opts.engine == "google":
        return _test_google()
    if opts.engine == "argos":
        return _test_argos(opts.lang_in, opts.lang_out)
    return False, f"未知引擎: {opts.engine}"


def _test_openai(opts: TranslateOptions) -> tuple[bool, str]:
    if not opts.base_url or not opts.api_key:
        return False, "未配置 API base_url 或 api_key"

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=normalize_base_url(opts.base_url),
            api_key=opts.api_key,
            timeout=20.0,
        )
        resp = client.chat.completions.create(
            model=opts.model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
        )
        if resp.choices:
            return True, f"API 连接成功（模型: {opts.model}）"
        return False, "API 返回了空响应"
    except Exception as e:
        detail = str(e)
        if "401" in detail or "Unauthorized" in detail:
            return False, f"API Key 无效（401）: {detail[:120]}"
        if "404" in detail or "not found" in detail.lower():
            return False, f"模型不存在（404）: 检查模型名 '{opts.model}'"
        if "Connection" in detail or "timeout" in detail.lower():
            return False, f"无法连接到 API: {detail[:120]}"
        return False, f"API 测试失败: {detail[:150]}"


def _test_google() -> tuple[bool, str]:
    try:
        import requests

        r = requests.get(
            "https://translate.google.com/m",
            params={"tl": "zh-CN", "sl": "en", "q": "Hi"},
            headers={"User-Agent": "Mozilla/4.0"},
            timeout=10,
        )
        if r.status_code == 200:
            return True, "Google 免费接口可用（需联网，无需 API Key）"
        return False, f"Google 接口返回 {r.status_code}"
    except Exception as e:
        return False, f"无法访问 Google（需联网）: {e}"


def _test_argos(lang_in: str, lang_out: str) -> tuple[bool, str]:
    try:
        import argostranslate.package

        installed = argostranslate.package.get_installed_packages()
        for pkg in installed:
            if pkg.from_code == lang_in and pkg.to_code == lang_out:
                return True, f"本地模型已就绪（{lang_in}→{lang_out}，完全离线）"
        return False, f"本地模型未安装（{lang_in}→{lang_out}），请先在设置中下载"
    except ImportError:
        return False, "argostranslate 未安装，请先 pip install argostranslate"
    except Exception as e:
        return False, f"检测失败: {e}"


# ── Argos 模型管理 ──────────────────────────────────────


def argos_status() -> dict:
    """返回 Argos 本地翻译模型的安装状态与可用语言对。"""
    try:
        import argostranslate.package

        installed = argostranslate.package.get_installed_packages()
        installed_pairs = sorted(
            {f"{p.from_code}->{p.to_code}" for p in installed}
        )
        try:
            argostranslate.package.update_package_index()
            available = argostranslate.package.get_available_packages()
            available_pairs = sorted(
                {f"{p.from_code}->{p.to_code}" for p in available}
            )
        except Exception:
            available_pairs = []
        return {
            "library_installed": True,
            "installed": installed_pairs,
            "available": available_pairs,
        }
    except ImportError:
        return {
            "library_installed": False,
            "installed": [],
            "available": [],
            "error": "argostranslate 未安装，请执行: pip install argostranslate",
        }
    except Exception as e:
        return {"library_installed": True, "installed": [], "available": [], "error": str(e)}


def argos_install(lang_in: str, lang_out: str) -> tuple[bool, str]:
    """下载并安装一个 Argos 语言对模型（首次需联网）。"""
    try:
        import argostranslate.package

        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        pkg = next(
            (
                p
                for p in available
                if p.from_code == lang_in and p.to_code == lang_out
            ),
            None,
        )
        if pkg is None:
            return False, f"Argos 不支持该语言对: {lang_in}→{lang_out}"
        argostranslate.package.install_from_path(pkg.download())
        return True, f"本地模型安装成功: {lang_in}→{lang_out}"
    except Exception as e:
        return False, f"安装失败: {e}"


# ── LibreOffice（DOCX/PPTX → PDF）───────────────────────

_LIBREOFFICE_PATHS = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/usr/bin/soffice",
    "/usr/local/bin/soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
]


def find_libreoffice(custom_path: str = "") -> Optional[Path]:
    if custom_path:
        p = Path(custom_path)
        if p.exists():
            return p
    found = shutil.which("soffice")
    if found:
        return Path(found)
    for p in _LIBREOFFICE_PATHS:
        if Path(p).exists():
            return Path(p)
    return None


def convert_to_pdf(source: Path, soffice: Path) -> Optional[Path]:
    """用 LibreOffice headless 把 DOCX/PPTX 等转成 PDF（临时文件）。"""
    tmp_dir = Path(tempfile.mkdtemp(prefix="linguapdf_"))
    try:
        result = subprocess.run(
            [
                str(soffice),
                "--headless",
                "--norestore",
                "--convert-to",
                "pdf",
                "--outdir",
                str(tmp_dir),
                str(source.resolve()),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.error("LibreOffice 转 PDF 失败: %s", result.stderr[:300])
            return None
        expected = tmp_dir / (source.stem + ".pdf")
        if expected.exists():
            return expected
        matches = list(tmp_dir.glob("*.pdf"))
        return matches[0] if matches else None
    except Exception as e:
        logger.error("LibreOffice 转 PDF 异常: %s", e)
        return None


# ── 核心翻译 ────────────────────────────────────────────


def translate_pdf(
    source_pdf: Path,
    output_dir: Optional[Path],
    opts: TranslateOptions,
    on_log: Optional[Callable[[str], None]] = None,
    thread: int = 4,
) -> TranslateResult:
    """翻译单个 PDF，输出保留原排版的译文 PDF。

    Args:
        output_dir: 输出目录；None 表示用源文件所在目录（"原路径"）。

    返回 files: [{name, path}]，含 <stem>_<lang_out>.pdf，
    dual=True 时另加 <stem>_dual.pdf（左右/上下双语对照）。
    """

    def _log(msg: str):
        logger.info(msg)
        if on_log:
            on_log(msg)

    t0 = time.monotonic()
    try:
        if opts.engine == "openai" and (not opts.base_url or not opts.api_key):
            return TranslateResult(error="未配置 API base_url 或 api_key")
        if not source_pdf.exists():
            return TranslateResult(error=f"源文件不存在: {source_pdf}")

        engine_label = {
            "openai": f"API（{opts.model}）",
            "google": "Google 免费接口",
            "argos": "本地离线模型",
        }.get(opts.engine, opts.engine)
        _log(f"开始翻译（引擎: {engine_label}）: {source_pdf.name}")

        _apply_tencentcloud_patch()
        from pdf2zh import translate_stream

        # 在子线程中确保有 asyncio 事件循环（pdf2zh 内部依赖 asyncio）
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        model = get_layout_model(on_log)
        pdf_bytes = source_pdf.read_bytes()

        envs = None
        if opts.engine == "openai":
            envs = {
                "OPENAI_BASE_URL": normalize_base_url(opts.base_url),
                "OPENAI_API_KEY": opts.api_key,
                "OPENAI_MODEL": opts.model,
            }

        mono_bytes, dual_bytes = translate_stream(
            stream=pdf_bytes,
            lang_in=opts.lang_in,
            lang_out=opts.lang_out,
            service=opts.engine,
            thread=thread,
            envs=envs,
            model=model,
        )

        # 输出目录：空 = 源文件所在目录（"原路径"），否则用指定目录
        out_dir = Path(output_dir) if output_dir else source_pdf.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        files = []
        mono_path = out_dir / f"{source_pdf.stem}_{opts.lang_out}.pdf"
        mono_path.write_bytes(mono_bytes)
        files.append({"name": mono_path.name, "path": str(mono_path)})
        if opts.dual and dual_bytes:
            dual_path = out_dir / f"{source_pdf.stem}_dual.pdf"
            dual_path.write_bytes(dual_bytes)
            files.append({"name": dual_path.name, "path": str(dual_path)})

        elapsed = time.monotonic() - t0
        _log(
            f"翻译完成: {source_pdf.name} → {len(files)} 个文件 ({elapsed:.1f}s)"
        )
        return TranslateResult(files=files, elapsed=elapsed)

    except Exception as e:
        elapsed = time.monotonic() - t0
        error_msg = f"{type(e).__name__}: {e}"
        logger.error("翻译失败: %s — %s", source_pdf.name, error_msg, exc_info=True)
        _log(f"翻译出错: {error_msg}")
        return TranslateResult(elapsed=elapsed, error=error_msg)
