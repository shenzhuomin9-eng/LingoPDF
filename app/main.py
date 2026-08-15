"""LingoPDF Web 服务。

启动: python run.py  或  uvicorn app.main:app --port 8377
"""

from __future__ import annotations

import asyncio
import io
import logging
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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
    engine: str | None = None
    base_url: str | None = None
    api_key: str | None = None   # 前端传 "****..." 形式时表示不修改
    model: str | None = None
    lang_in: str | None = None
    lang_out: str | None = None
    thread: int | None = None
    dual: bool | None = None
    output_dir: str | None = None
    libreoffice_path: str | None = None
    ui_lang: str | None = None


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


@app.post("/api/translate")
async def create_translation(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, "未收到文件")

    saved = cfg.load_config()
    opts = TranslateOptions(
        engine=saved["engine"],
        base_url=saved["base_url"],
        api_key=saved["api_key"],
        model=saved["model"],
        lang_in=saved["lang_in"],
        lang_out=saved["lang_out"],
        dual=bool(saved.get("dual")),
    )
    if opts.engine == "openai" and (not opts.base_url or not opts.api_key):
        raise HTTPException(400, "当前引擎为 API 翻译，请先在设置中配置 base_url 和 api_key")

    saved_files = []
    import uuid as _uuid
    import tempfile

    # 先生成 job_id，用它做上传目录（与 create_job 的 id 保持一致）
    job_id = _uuid.uuid4().hex[:12]
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        if ext not in ACCEPT_EXTS:
            raise HTTPException(400, f"不支持的文件类型: {f.filename}")
        data = await f.read()
        if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(400, f"文件超过 {MAX_UPLOAD_MB}MB: {f.filename}")
        dest = job_dir / Path(f.filename).name
        dest.write_bytes(data)
        saved_files.append((f.filename, dest, len(data)))

    job = manager.create_job(saved_files, opts, int(saved.get("thread", 4)), job_id=job_id)
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
        raise HTTPException(404, "任务不存在")
    outputs = [o for f in job.files for o in f.outputs]
    if not outputs:
        raise HTTPException(404, "没有可下载的结果")
    zip_path = UPLOAD_DIR / job_id / "results.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for o in outputs:
            zf.write(o["path"], arcname=Path(o["path"]).name)
    return FileResponse(
        zip_path,
        filename=f"linguapdf_{job_id}.zip",
        media_type="application/zip",
    )


@app.get("/api/jobs/{job_id}/files/{file_index}/{out_index}")
def download_file(job_id: str, file_index: int, out_index: int):
    job = manager.get(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    try:
        jf = job.files[file_index]
        out = jf.outputs[out_index]
    except IndexError:
        raise HTTPException(404, "文件不存在")
    return FileResponse(out["path"], filename=out["name"], media_type="application/pdf")


# 静态前端（放最后，避免吞掉 /api）
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
