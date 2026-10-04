"""LingoPDF Web 服务。

启动: python run.py  或  uvicorn app.main:app --port 8377
"""

from __future__ import annotations

import asyncio
import io
import logging
import tempfile
import zipfile
import json
import shutil
import subprocess
import sys
import threading
from typing import Literal
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .storage import register_sources, resolve_source, save_outputs

from . import config as cfg
from .jobs import ACCEPT_EXTS, manager
from .translator import (
    TranslateOptions,
    argos_install,
    argos_status,
    test_connection,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("linguapdf")

app = FastAPI(title="LingoPDF", docs_url=None, redoc_url=None)

# 禁用静态文件缓存，确保用户总是拿到最新前端代码
from starlette.middleware.base import BaseHTTPMiddleware

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Browsers on foreign sites must not operate the local file APIs.
        if request.url.path.startswith('/api'):
            origin = request.headers.get('origin')
            if origin and origin != str(request.base_url).rstrip('/'):
                return JSONResponse({'detail': 'Foreign origin is not allowed'}, status_code=403)
        response = await call_next(request)
        if request.url.path.startswith("/api"):
            return response
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_MB = 200


# ── 配置 ────────────────────────────────────────────────


class ConfigPayload(BaseModel):
    engine: Literal['google', 'openai', 'argos'] | None = None
    base_url: str | None = None
    api_key: str | None = None   # 前端传 "****..." 形式时表示不修改
    model: str | None = None
    lang_in: Literal['en', 'zh', 'ja', 'ko', 'fr', 'de', 'ru', 'es'] | None = None
    lang_out: Literal['en', 'zh', 'ja', 'ko', 'fr', 'de', 'ru', 'es'] | None = None
    thread: int | None = Field(default=None, ge=1, le=16)
    dual: bool | None = None
    skip_references: bool | None = None
    output_dir: str | None = None
    libreoffice_path: str | None = None
    ui_lang: Literal['en', 'zh'] | None = None


@app.get("/api/config")
def get_config():
    return cfg.masked(cfg.load_config())


@app.post("/api/config")
def update_config(payload: ConfigPayload):
    updates = payload.model_dump(exclude_none=True)
    # 打码后的 key 不覆盖真实 key
    api_key = updates.get("api_key")
    if api_key is not None and "*" in api_key:
        updates.pop("api_key")
    if "engine" in updates and updates["engine"] not in cfg.ENGINES:
        raise HTTPException(400, f"不支持的引擎，可选: {', '.join(cfg.ENGINES)}")
    if updates.get('output_dir') and not Path(updates['output_dir']).expanduser().is_absolute():
        raise HTTPException(400, '输出目录需要绝对路径')
    cfg.save_config(updates)
    return cfg.masked(cfg.load_config())


# ── 引擎 ────────────────────────────────────────────────


class TestPayload(BaseModel):
    engine: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    lang_in: str | None = None
    lang_out: str | None = None


@app.post("/api/test-connection")
async def test_conn(payload: TestPayload):
    """测试翻译引擎可用性。未传的字段落回已保存配置。"""
    saved = cfg.load_config()

    def _run():
        return test_connection(
            TranslateOptions(
                engine=payload.engine or saved["engine"],
                base_url=payload.base_url or saved["base_url"],
                api_key=(payload.api_key if payload.api_key and "*" not in payload.api_key else saved["api_key"]),
                model=payload.model or saved["model"],
                lang_in=payload.lang_in or saved["lang_in"],
                lang_out=payload.lang_out or saved["lang_out"],
            )
        )

    ok, msg = await asyncio.to_thread(_run)
    return {"ok": ok, "message": msg}


@app.get("/api/engines")
def engines_info():
    return {
        "engines": [
            {"id": "openai", "name": "API 翻译", "desc": "OpenAI 兼容接口（DeepSeek/GLM/OpenAI 等），质量最高，需 API Key"},
            {"id": "google", "name": "Google 免费", "desc": "免费网页接口，无需 Key，需联网"},
            {"id": "argos", "name": "本地离线", "desc": "Argos 本地模型，断网可用，轻量，质量中等"},
        ],
        "argos": argos_status(),
    }


@app.post("/api/engines/argos/install")
async def argos_install_ep(lang_in: str = "en", lang_out: str = "zh"):
    ok, msg = await asyncio.to_thread(argos_install, lang_in, lang_out)
    return {"ok": ok, "message": msg}


# ── 翻译任务 ────────────────────────────────────────────


class LocalFilesPayload(BaseModel):
    paths: list[str] = Field(min_length=1, max_length=100)


@app.post('/api/local-files')
async def import_local_files(payload: LocalFilesPayload):
    try:
        records = await asyncio.to_thread(register_sources, payload.paths)
        return {'files': records}
    except (ValueError, OSError) as exc:
        raise HTTPException(400, str(exc))


@app.post('/api/local-files/pick')
async def pick_local_files():
    def pick():
        global _picker_process
        with _picker_lock:
            if _picker_process and _picker_process.poll() is None:
                raise ValueError('文件选择窗口已打开。 / A file picker is already open.')
            process = subprocess.Popen([getattr(sys, '_base_executable', sys.executable),
                                        str(Path(__file__).parent / 'file_dialog.py')],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                       creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            _picker_process = process
        try:
            stdout, _ = process.communicate(timeout=180)
            if process.returncode and not stdout:
                return []  # User canceled through the browser.
            paths = json.loads(stdout)
            if process.returncode or not isinstance(paths, list):
                raise ValueError('无法打开系统文件选择器，请使用原路径导入。 / Use path import instead.')
            return paths
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            with _picker_lock:
                if _picker_process is process:
                    _picker_process = None
    try:
        paths = await asyncio.to_thread(pick)
        return {'files': await asyncio.to_thread(register_sources, paths) if paths else []}
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        raise HTTPException(400, str(exc))


_picker_lock = threading.Lock()
_picker_process = None


@app.post('/api/local-files/pick-cancel')
def cancel_file_picker():
    with _picker_lock:
        if _picker_process and _picker_process.poll() is None:
            _picker_process.terminate()
    return {'ok': True}


@app.post("/api/translate")
async def create_translation(files: list[UploadFile] = File(default=[]),
                             entries: str = Form(''), lang_in: str = Form(''), lang_out: str = Form(''),
                             dual: bool | None = Form(None), skip_references: bool | None = Form(None)):

    saved = cfg.load_config()
    languages = {'en', 'zh', 'ja', 'ko', 'fr', 'de', 'ru', 'es'}
    source, target = lang_in or saved['lang_in'], lang_out or saved['lang_out']
    if source not in languages or target not in languages or source == target:
        raise HTTPException(400, '请选择不同的有效源语言和目标语言。 / Choose different source and target languages.')
    opts = TranslateOptions(
        engine=saved["engine"],
        base_url=saved["base_url"],
        api_key=saved["api_key"],
        model=saved["model"],
        lang_in=source,
        lang_out=target,
        dual=dual if dual is not None else bool(saved.get("dual")),
        skip_references=skip_references if skip_references is not None else bool(saved.get('skip_references', True)),
        output_dir=saved.get('output_dir', ''),
    )
    if opts.engine == "openai" and (not opts.base_url or not opts.api_key):
        raise HTTPException(400, "当前引擎为 API 翻译，请先在设置中配置 base_url 和 api_key")

    import uuid as _uuid
    try:
        manifest = json.loads(entries) if entries else [{'upload': i} for i in range(len(files))]
        if not isinstance(manifest, list) or not manifest or len(manifest) > 100:
            raise ValueError('请选择 1–100 个文件')
        if not all(isinstance(entry, dict) for entry in manifest):
            raise ValueError('无效的文件列表')
    except (ValueError, TypeError) as exc:
        raise HTTPException(400, str(exc))

    # 先生成 job_id，用它做上传目录（与 create_job 的 id 保持一致）
    job_id = _uuid.uuid4().hex[:12]
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    sources = []
    try:
        for i, entry in enumerate(manifest):
            folder = job_dir / str(i)
            folder.mkdir()
            if 'id' in entry:
                original = resolve_source(entry['id'])
                dest = folder / original.name
                await asyncio.to_thread(shutil.copyfile, original, dest)
                size = dest.stat().st_size
                name = original.name
                sources.append((original, entry['id']))
            else:
                index = entry.get('upload')
                if not isinstance(index, int) or index < 0 or index >= len(files):
                    raise ValueError('无效的上传文件标识')
                f = files[index]
                name = Path((f.filename or '').replace('\\', '/')).name
                if Path(name).suffix.lower() not in ACCEPT_EXTS:
                    raise ValueError(f'不支持的文件类型: {name}')
                dest = folder / name
                size = 0
                with dest.open('wb') as writer:
                    while chunk := await f.read(1024 * 1024):
                        size += len(chunk)
                        if size > MAX_UPLOAD_MB * 1024 * 1024:
                            raise ValueError(f'文件超过 200MB: {name}')
                        writer.write(chunk)
                sources.append((None, None))
            if not size:
                raise ValueError(f'文件为空: {name}')
            saved_files.append((name, dest, size))
    except (ValueError, OSError, TypeError) as exc:
        shutil.rmtree(job_dir)
        raise HTTPException(400, str(exc))
    finally:
        for f in files:
            await f.close()

    job = manager.create_job(saved_files, opts, max(1, min(16, int(saved.get("thread", 4)))), job_id=job_id, sources=sources)
    return {"job_id": job.id, "files": len(saved_files)}


@app.get("/api/jobs")
def list_jobs():
    return [
        {"id": j.id, "status": j.status, "created_at": j.created_at, "files": len(j.files)}
        for j in manager.all_jobs()
    ]


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str, since_log: int = 0):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    return job.to_dict(since_log=since_log)


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    if not manager.cancel(job_id):
        raise HTTPException(400, "任务不可取消（可能已结束）")
    return {"ok": True}


@app.get("/api/jobs/{job_id}/download-all")
def download_all(job_id: str):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    outputs = [o for f in job.files for o in f.outputs]
    if not outputs:
        raise HTTPException(404, "No files to download")
    # 单个文件直接下载 PDF，多个文件才打 zip
    if len(outputs) == 1:
        o = outputs[0]
        return FileResponse(o["path"], filename=Path(o["path"]).name, media_type="application/pdf")
    # 多个文件打包 zip
    zip_path = UPLOAD_DIR / job_id / "results.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        names = set()
        for o in outputs:
            name = Path(o['name']).name
            counter = 0
            while name in names:
                counter += 1
                name = f"{Path(o['name']).stem} ({counter}){Path(o['name']).suffix}"
            names.add(name)
            zf.write(o["path"], arcname=name)
    return FileResponse(
        zip_path,
        filename=f"linguapdf_{job_id}.zip",
        media_type="application/zip",
    )


@app.post('/api/jobs/{job_id}/save-all')
def save_all(job_id: str):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, '任务不存在')
    if job.status in ('queued', 'running', 'canceling'):
        raise HTTPException(409, '请等待任务完成后保存')
    if not any(f.outputs for f in job.files):
        raise HTTPException(400, '没有可保存的译文')
    return save_outputs(job)


@app.get("/api/jobs/{job_id}/files/{file_index}/{out_index}")
def download_file(job_id: str, file_index: int, out_index: int):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    if file_index < 0 or out_index < 0:
        raise HTTPException(404, '文件不存在')
    try:
        jf = job.files[file_index]
        out = jf.outputs[out_index]
    except IndexError:
        raise HTTPException(404, "文件不存在")
    return FileResponse(out["path"], filename=out["name"], media_type="application/pdf")


# ── 文件语言检测 ─────────────────────────────────────────


@app.post("/api/detect-lang")
async def detect_lang_endpoint(
    job_id: str = Form(None),
    file_index: str = Form(None),
    file: UploadFile = File(None),
):
    """检测 PDF 文件的源语言。接受两种模式：
    1. job_id + file_index → 检测已上传/saved 的文件
    2. file blob（直接上传）→ 检测临时文件
    """
    from .translator import detect_pdf_lang

    lang_names = {
        "en": "English",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ru": "Russian",
    }

    # 模式 1：检测已上传文件
    if job_id and file_index is not None:
        job = manager.get(job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        try:
            idx = int(file_index)
        except (ValueError, TypeError):
            raise HTTPException(400, "Invalid file index")
        
        if idx < 0 or idx >= len(job.files):
            raise HTTPException(400, "Invalid file index")
        
        upload_path = job.files[idx].upload_path
        detected = await asyncio.to_thread(detect_pdf_lang, upload_path)
        return {
            "detected": detected,
            "detected_name": lang_names.get(detected, detected) if detected else "Unidentified",
        }

    # 模式 2：直接上传文件 blob
    if file:
        if file.content_type and 'pdf' not in file.content_type.lower():
            raise HTTPException(400, "Only PDF files are supported")
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            content = await file.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
            if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
                raise HTTPException(400, '文件超过 200MB')
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            detected = await asyncio.to_thread(detect_pdf_lang, tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
        return {
            "detected": detected,
            "detected_name": lang_names.get(detected, detected) if detected else "Unidentified",
        }

    raise HTTPException(400, "Must provide either job_id+file_index or file")


# ── 远程关闭（浏览器关闭即关服务）─────────────────────────

import os
import signal
import threading
import time

_last_heartbeat = time.time()
_shutdown_requested_at = None
_lock = threading.Lock()


@app.post("/api/heartbeat")
async def heartbeat():
    """前端定期心跳，用于判断浏览器是否还开着。"""
    global _last_heartbeat
    with _lock:
        _last_heartbeat = time.time()
    return {"ok": True}


@app.post("/api/shutdown")
async def shutdown_server():
    """前端在页面关闭时调用。后端延迟 2 秒后检查：
    如果 shutdown 之后没有新的心跳（浏览器真关了）→ 退出进程；
    如果有心跳（页面刷新后重新加载）→ 不退出。"""
    global _shutdown_requested_at
    with _lock:
        _shutdown_requested_at = time.time()

    def _delayed_kill():
        time.sleep(2.0)
        if any(j.status in ('queued', 'running', 'canceling') for j in manager.all_jobs()):
            return
        with _lock:
            # shutdown 之后又收到新心跳 = 页面刷新，不关
            if _last_heartbeat > _shutdown_requested_at:
                return
        try:
            os.kill(os.getpid(), signal.SIGINT)
        except Exception:
            import sys
            sys.exit(0)

    threading.Thread(target=_delayed_kill, daemon=True).start()
    return {"ok": True}


# 静态前端（放最后，避免吞掉 /api）
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
