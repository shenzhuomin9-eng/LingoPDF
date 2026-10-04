"""批量翻译任务管理：上传 → 后台线程逐文件翻译 → 状态轮询。

一个 Job 对应一次「开始翻译」，包含多个文件。
状态通过 GET /api/jobs/{id} 轮询，日志走环形缓冲。
"""

from __future__ import annotations

import logging
import json
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
    source_path: Optional[Path] = None
    source_id: Optional[str] = None
    reference_pages: int = 0
    status: str = "pending"      # pending | converting | translating | done | failed | canceled
    error: Optional[str] = None
    elapsed: float = 0.0
    progress: float = 0.0        # 翻译页级进度 0.0 ~ 1.0
    outputs: list[dict] = field(default_factory=list)  # [{name, path}]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "size": self.size,
            "status": self.status,
            "error": self.error,
            "elapsed": round(self.elapsed, 1),
            "progress": round(self.progress, 2),
            "outputs": self.outputs,
            "source_path": str(self.source_path) if self.source_path else None,
            "source_id": self.source_id,
            "reference_pages": self.reference_pages,
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
    document_parallel: int = 1
    logs: deque = field(default_factory=lambda: deque(maxlen=800))
    log_seq: int = 0
    cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)
    log_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add_log(self, msg: str, level: str = "info"):
        with self.log_lock:
            self.log_seq += 1
            self.logs.append(
                {"seq": self.log_seq, "ts": time.time(), "level": level, "msg": msg}
            )

    def to_dict(self, since_log: int = 0) -> dict:
        done = sum(1 for f in self.files if f.status in ("done", "failed", "canceled"))
        with self.log_lock:
            logs = [l for l in self.logs if l["seq"] > since_log]
            log_seq = self.log_seq
        return {
            "id": self.id,
            "status": self.status,
            "engine": self.opts.engine,
            "lang_in": self.opts.lang_in,
            "lang_out": self.opts.lang_out,
            "output_dir": self.opts.output_dir,
            "dual": self.opts.dual,
            "skip_references": self.opts.skip_references,
            "document_parallel": self.document_parallel,
            "thread": self.thread,
            "files": [f.to_dict() for f in self.files],
            "progress": {
                "total": len(self.files),
                "done": done,
                "ok": sum(1 for f in self.files if f.status == "done"),
                "failed": sum(1 for f in self.files if f.status == "failed"),
                "fraction": sum(1 if f.status in ('done', 'failed', 'canceled') else f.progress for f in self.files) / max(1, len(self.files)),
            },
            "logs": logs,
            "log_seq": log_seq,
            "created_at": self.created_at,
            "elapsed": (
                round((self.finished_at or time.time()) - self.started_at, 1)
                if self.started_at
                else 0
            ),
        }


class JobManager:
    """全局任务管理器（进程内单例）。"""

    def __init__(self, history_dir: Optional[Path] = None):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._threads: list[threading.Thread] = []
        self._execution_lock = threading.Lock()
        self._load_history(history_dir or cfg.project_root() / 'data' / 'uploads')

    def _load_history(self, root: Path):
        """Restore completed jobs without restoring API credentials or starting work."""
        manifests = sorted(root.glob('*/job.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        for manifest in manifests[:100]:
            try:
                data = json.loads(manifest.read_text(encoding='utf-8'))
                if data['id'] != manifest.parent.name or data['status'] not in ('finished', 'failed', 'canceled'):
                    continue
                files = []
                for index, item in enumerate(data['files']):
                    name = Path(item['name']).name
                    jf = JobFile(name=name, upload_path=manifest.parent / str(index) / name, size=item['size'])
                    jf.source_path = Path(item['source_path']) if item.get('source_path') else None
                    jf.source_id = item.get('source_id')
                    jf.status = item['status']
                    jf.error = item.get('error')
                    jf.elapsed = item.get('elapsed', 0)
                    jf.progress = item.get('progress', 0)
                    jf.reference_pages = item.get('reference_pages', 0)
                    for output in item.get('outputs', []):
                        path = Path(output['path']).resolve()
                        if path.is_relative_to(manifest.parent.resolve()) and path.is_file():
                            jf.outputs.append({'name': path.name, 'path': str(path)})
                    files.append(jf)
                opts = TranslateOptions(**{key: data[key] for key in
                    ('engine', 'lang_in', 'lang_out', 'output_dir', 'dual', 'skip_references') if key in data})
                job = Job(id=data['id'], files=files, opts=opts, thread=4, status=data['status'],
                          created_at=data.get('created_at', manifest.stat().st_mtime))
                job.started_at = job.created_at
                job.document_parallel = data.get('document_parallel', 1)
                job.finished_at = job.created_at + data.get('elapsed', 0)
                job.logs.extend(data.get('logs', []))
                job.log_seq = data.get('log_seq', 0)
                self._jobs[job.id] = job
            except (OSError, ValueError, KeyError, TypeError):
                logger.warning('Cannot restore job metadata: %s', manifest.parent.name)

    # ── 提交 ──────────────────────────────────────────

    def create_job(
        self, files: list[tuple[str, Path, int]], opts: TranslateOptions, thread: int,
        job_id: str = None,
        sources: Optional[list[tuple[Optional[Path], Optional[str]]]] = None,
    ) -> Job:
        job_id = job_id or uuid.uuid4().hex[:12]
        job = Job(
            id=job_id,
            files=[JobFile(name=n, upload_path=p, size=s) for n, p, s in files],
            opts=opts,
            thread=thread,
        )
        for jf, (source_path, source_id) in zip(job.files, sources or []):
            jf.source_path, jf.source_id = source_path, source_id
        with self._lock:
            self._jobs[job_id] = job
        t = threading.Thread(target=self._run, args=(job,), daemon=True)
        t.start()
        self._threads.append(t)
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def all_jobs(self) -> list[Job]:
        with self._lock:
            return sorted(list(self._jobs.values()), key=lambda j: j.created_at, reverse=True)

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job.status in ("queued", "running"):
            job.status = "canceling"
            job.cancel_event.set()
            job.add_log(_("cancel_sent"), "warn")
            return True
        return False

    # ── 执行 ──────────────────────────────────────────

    def _run(self, job: Job):
        # Keep model inference and font/cache initialization in one document worker.
        while not self._execution_lock.acquire(timeout=0.1):
            if job.cancel_event.is_set():
                for jf in job.files:
                    jf.status = 'canceled'
                job.finished_at = time.time()
                job.status = 'canceled'
                self._persist_job(job)
                return
        try:
            self._execute(job)
        finally:
            self._execution_lock.release()

    @staticmethod
    def _persist_job(job):
        if job.files:
            manifest = job.files[0].upload_path.parent.parent / 'job.json'
            try:
                manifest.parent.mkdir(parents=True, exist_ok=True)
                manifest.write_text(json.dumps(job.to_dict(), ensure_ascii=False, indent=2), encoding='utf-8')
            except OSError:
                logger.warning('Cannot persist job metadata: %s', job.id)

    def _execute(self, job: Job):
        # 子线程必须有 asyncio 事件循环（pdf2zh 内部依赖）
        # Windows 子线程用 SelectorEventLoop 避免 [Errno 22]
        import asyncio as _a
        import sys as _sys
        if _sys.platform == "win32":
            _a.set_event_loop_policy(_a.WindowsSelectorEventLoopPolicy())
        try:
            _loop = _a.get_event_loop()
            if _loop.is_closed():
                raise RuntimeError("loop closed")
        except RuntimeError:
            _loop = _a.new_event_loop()
            _a.set_event_loop(_loop)

        if job.cancel_event.is_set():
            for jf in job.files:
                jf.status = 'canceled'
            job.finished_at = time.time()
            job.status = 'canceled'
            self._persist_job(job)
            _loop.close()
            return
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

        from . import pipeline
        pipeline.request_budget.configure(job.thread)
        parallel = (job.opts.engine == 'openai' and job.thread >= 2 and len(job.files) >= 2
                    and max(f.size for f in job.files) <= 25 * 1024**2
                    and pipeline.available_memory() >= 2 * 1024**3 and pipeline.supported())
        job.document_parallel = 2 if parallel else 1
        if parallel:
            job.add_log(f'API 文档交错处理：最多 2 份；PDF 排版单线程；总请求并发上限 {job.thread}')
        elif job.opts.engine == 'openai' and len(job.files) >= 2:
            if pipeline.available_memory() < 2 * 1024**3:
                job.add_log('可用内存不足 2 GB，自动逐份处理，避免占用过多内存。')
            elif job.thread < 2:
                job.add_log('请求并发设为 1，逐份处理；可在设置中调整请求并发总额。')
            else:
                job.add_log('文档较大或当前引擎不支持流水线，自动逐份处理。')
        workers = max(1, job.thread // job.document_parallel)
        try:
            pipeline.run_documents([lambda jf=jf: self._process_file(job, jf, soffice, workers)
                                    for jf in job.files], max_active=job.document_parallel)
        except Exception as error:
            logger.exception('Document pipeline failed: %s', job.id)
            for jf in job.files:
                if jf.status in ('pending', 'converting', 'translating'):
                    jf.status, jf.error = 'failed', str(error)

        job.status = 'canceled' if job.cancel_event.is_set() else 'finished'
        job.finished_at = time.time()
        ok = sum(1 for f in job.files if f.status == "done")
        fail = sum(1 for f in job.files if f.status == "failed")
        job.add_log(_("job_end", ok=ok, fail=fail))
        # Persist paths and result metadata, never provider credentials.
        self._persist_job(job)
        _loop.close()

    @staticmethod
    def _process_file(job, jf, soffice, workers):
        if job.cancel_event.is_set():
            jf.status = 'canceled'
            return
        try:
            pdf_source = jf.upload_path
            if pdf_source.suffix.lower() != '.pdf':
                if soffice is None:
                    jf.status, jf.error = 'failed', _("no_libreoffice_err")
                    return
                jf.status = 'converting'
                job.add_log(_("converting", name=jf.name))
                pdf_source = convert_to_pdf(pdf_source, soffice)
                if pdf_source is None:
                    jf.status, jf.error = 'failed', _("convert_failed")
                    return
            jf.status, jf.progress = 'translating', 0.0
            result = translate_pdf(pdf_source, jf.upload_path.parent / 'results', job.opts,
                on_log=lambda message: job.add_log(f'[{jf.name}] {message}'), thread=workers,
                on_progress=lambda fraction: setattr(jf, 'progress', fraction), cancel_event=job.cancel_event)
            jf.progress, jf.elapsed = 1.0, result.elapsed
            if result.canceled or job.cancel_event.is_set():
                jf.status = 'canceled'
            elif result.success:
                jf.status, jf.outputs, jf.reference_pages = 'done', result.files, result.reference_pages
            else:
                jf.status, jf.error = 'failed', result.error
        except Exception as error:
            jf.status, jf.error = 'failed', f'{type(error).__name__}: {error}'
            logger.exception('任务文件处理异常: %s', jf.name)


manager = JobManager()
