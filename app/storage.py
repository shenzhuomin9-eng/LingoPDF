"""Verified local input records and explicit, collision-safe result export."""
from __future__ import annotations

import json
import shutil
import threading
import uuid
from pathlib import Path

from . import config as cfg

SOURCE_DIR = cfg.project_root() / 'data' / 'sources'
_lock = threading.Lock()
MAX_BYTES = 200 * 1024 * 1024


def register_sources(paths: list[str]) -> list[dict]:
    from .jobs import ACCEPT_EXTS
    verified = []
    for value in paths:
        path = Path(value.strip().strip('"')).expanduser()
        if not path.is_absolute() or not path.is_file():
            raise ValueError(f'文件不存在或不是绝对路径: {value}')
        path = path.resolve()
        if path.suffix.lower() not in ACCEPT_EXTS:
            raise ValueError(f'不支持的文件类型: {path.name}')
        size = path.stat().st_size
        if size > MAX_BYTES:
            raise ValueError(f'文件超过 200MB: {path.name}')
        if size == 0:
            raise ValueError(f'文件为空: {path.name}')
        verified.append((path, size))
    results = []
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    for path, size in verified:
        record = {'id': uuid.uuid4().hex, 'name': path.name, 'size': size,
                  'source_path': str(path)}
        (SOURCE_DIR / f"{record['id']}.json").write_text(
            json.dumps(record, ensure_ascii=False), encoding='utf-8')
        results.append(record)
    return results


def resolve_source(source_id: str) -> Path:
    if len(source_id) != 32 or any(c not in '0123456789abcdef' for c in source_id):
        raise ValueError('无效的本地文件标识')
    record_path = SOURCE_DIR / f'{source_id}.json'
    if not record_path.is_file():
        raise ValueError('本地文件记录已失效，请重新导入')
    record = json.loads(record_path.read_text(encoding='utf-8'))
    path = Path(record['source_path'])
    if not path.is_file():
        raise ValueError(f'原文件已移动或删除: {path}')
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('原文件超过 200MB')
    return path


def save_outputs(job) -> dict:
    saved, errors = [], []
    with _lock:
        for jf in job.files:
            root = (Path(job.opts.output_dir).expanduser() if job.opts.output_dir
                    else jf.source_path.parent if jf.source_path
                    else cfg.default_output_dir())
            destination = root / 'LingoPDF'
            for output in jf.outputs:
                try:
                    destination.mkdir(parents=True, exist_ok=True)
                    name = Path(output['name']).name
                    stem, suffix = Path(name).stem, Path(name).suffix
                    counter = 0
                    while True:
                        target = destination / (name if counter == 0 else f'{stem} ({counter}){suffix}')
                        try:
                            with target.open('xb') as writer:
                                try:
                                    with Path(output['path']).open('rb') as reader:
                                        shutil.copyfileobj(reader, writer)
                                except Exception:
                                    writer.close()
                                    target.unlink(missing_ok=True)
                                    raise
                            break
                        except FileExistsError:
                            counter += 1
                    saved.append({'name': target.name, 'path': str(target.resolve()),
                                  'source_path': str(jf.source_path) if jf.source_path else None,
                                  'fallback': not jf.source_path and not job.opts.output_dir})
                except OSError as exc:
                    errors.append({'name': output['name'], 'error': str(exc)})
    return {'saved': saved, 'errors': errors, 'folders': sorted({str(Path(s['path']).parent) for s in saved})}
