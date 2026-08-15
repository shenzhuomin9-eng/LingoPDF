"""批量翻译任务管理：上传 → 后台线程逐文件翻译 → 状态轮询。

一个 Job 对应一次「开始翻译」，包含多个文件。
状态通过 GET /api/jobs/{id} 轮询，日志走环形缓冲。
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import config as cfg
from .i18n import msg as _
from .translator import (
    TranslateOptions,
    convert_to_pdf,
    find_libreoffice,
    translate_pdf,
)

logger = logging.getLogger(__name__)

# 允许上传的扩展名（PDF 直译；其余经 LibreOffice 转 PDF）
ACCEPT_EXTS = {".pdf", ".docx", ".pptx", ".doc", ".ppt"}


@dataclass
class JobFile:
    name: str
    upload_path: Path
    size: int
    status: str = "pending"      # pending | converting | translating | done | failed | canceled
    error: Optional[str] = None
    elapsed: float = 0.0
    outputs: list[dict] = field(default_factory=list)  # [{name, path}]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "size": self.size,
            "status": self.status,
            "error": self.error,
            "elapsed": round(self.elapsed, 1),
            "outputs": self.outputs,
        }


@dataclass
class Job:
    id: str
    files: list[JobFile]
    opts: TranslateOptions
    thread: int
    status: str = "queued"       # queued | running | finished | canceled | failed
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    logs: deque = field(default_factory=lambda: deque(maxlen=800))
    log_seq: int = 0

    def add_log(self, msg: str, level: str = "info"):
        self.log_seq += 1
        self.logs.append(
            {"seq": self.log_seq, "ts": time.time(), "level": level, "msg": msg}
        )

    def to_dict(self, since_log: int = 0) -> dict:
        done = sum(1 for f in self.files if f.status in ("done", "failed", "canceled"))
        return {
            "id": self.id,
            "status": self.status,
            "engine": self.opts.engine,
            "lang_in": self.opts.lang_in,
            "lang_out": self.opts.lang_out,
            "files": [f.to_dict() for f in self.files],
            "progress": {
                "total": len(self.files),
                "done": done,
                "ok": sum(1 for f in self.files if f.status == "done"),
                "failed": sum(1 for f in self.files if f.status == "failed"),
            },
            "logs": [l for l in self.logs if l["seq"] > since_log],
            "log_seq": self.log_seq,
            "created_at": self.created_at,
            "elapsed": (
                round((self.finished_at or time.time()) - self.started_at, 1)
                if self.started_at
                else 0
            ),
        }


class JobManager:
    """全局任务管理器（进程内单例）。"""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._threads: list[threading.Thread] = []

    # ── 提交 ──────────────────────────────────────────

    def create_job(
        self, files: list[tuple[str, Path, int]], opts: TranslateOptions, thread: int,
        job_id: str = None,
    ) -> Job:
        job_id = job_id or uuid.uuid4().hex[:12]
        job = Job(
            id=job_id,
            files=[JobFile(name=n, upload_path=p, size=s) for n, p, s in files],
            opts=opts,
            thread=thread,
        )
        with self._lock:
            self._jobs[job_id] = job
        t = threading.Thread(target=self._run, args=(job,), daemon=True)
        t.start()
        self._threads.append(t)
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def all_jobs(self) -> list[Job]:
        return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job.status in ("queued", "running"):
            job.status = "canceled"
            job.add_log(_("cancel_sent"), "warn")
            return True
        return False

    # ── 执行 ──────────────────────────────────────────

    def _run(self, job: Job):
        # 子线程必须有 asyncio 事件循环（pdf2zh 内部依赖）
        import asyncio as _a
        try:
            _a.get_event_loop()
        except RuntimeError:
            _a.set_event_loop(_a.new_event_loop())

        job.status = "running"
        job.started_at = time.time()
        job.add_log(_("job_start", n=len(job.files)))

        # 非 PDF 文件需要 LibreOffice
        need_convert = any(
            f.upload_path.suffix.lower() != ".pdf" for f in job.files
        )
        soffice = None
        if need_convert:
            soffice = find_libreoffice(cfg.load_config().get("libreoffice_path", ""))
            if soffice is None:
                job.add_log(_("no_libreoffice"), "warn")

        # 输出目录：空 = 源文件原路径；否则用指定目录
        cfg_output_dir = cfg.load_config().get("output_dir", "")

        for i, jf in enumerate(job.files):
            if job.status == "canceled":
                for rest in job.files[i:]:
                    if rest.status == "pending":
                        rest.status = "canceled"
                break

            try:
                pdf_source = jf.upload_path
                if pdf_source.suffix.lower() != ".pdf":
                    if soffice is None:
                        jf.status = "failed"
                        jf.error = _("no_libreoffice_err")
                        continue
                    jf.status = "converting"
                    job.add_log(_("converting", name=jf.name))
                    pdf_source = convert_to_pdf(pdf_source, soffice)
                    if pdf_source is None:
                        jf.status = "failed"
                        jf.error = _("convert_failed")
                        continue

                jf.status = "translating"
                # 原路径模式：传空让 translate_pdf 用源文件所在目录
                # 上传的文件在 data/uploads/<jobid>/ 下，"原路径"指那里
                # 指定目录模式：在该目录下为每个文件建子目录
                if cfg_output_dir:
                    out_dir = Path(cfg_output_dir) / jf.upload_path.stem
                else:
                    out_dir = None  # None → translate_pdf 用 source_pdf.parent
                result = translate_pdf(
                    pdf_source,
                    out_dir,
                    job.opts,
                    on_log=lambda m, _n=jf.name: job.add_log(f"[{_n}] {m}"),
                    thread=job.thread,
                )
                jf.elapsed = result.elapsed
                if result.success:
                    jf.status = "done"
                    jf.outputs = result.files
                else:
                    jf.status = "failed"
                    jf.error = result.error
            except Exception as e:
                jf.status = "failed"
                jf.error = f"{type(e).__name__}: {e}"
                logger.exception("任务文件处理异常: %s", jf.name)

        if job.status != "canceled":
            job.status = "finished"
        job.finished_at = time.time()
        ok = sum(1 for f in job.files if f.status == "done")
        fail = sum(1 for f in job.files if f.status == "failed")
        job.add_log(_("job_end", ok=ok, fail=fail))


manager = JobManager()
