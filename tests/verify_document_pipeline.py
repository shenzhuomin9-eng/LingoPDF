"""Optional integration check: two tiny real PDFs, configured provider and cache.

The memory probe is overridden only for these 3 KB fixtures, so the actual
cooperative PDF pipeline can be checked even on a busy development computer.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
import threading
import time
from unittest.mock import patch
import fitz
from app import config, engine_guard, pipeline
from app.translator import TranslateOptions, translate_pdf

root = config.project_root()
settings = config.load_config()
opts = TranslateOptions(**{key: settings[key] for key in
    ('engine', 'base_url', 'api_key', 'model')}, lang_in='en', lang_out='zh',
    skip_references=True, dual=True)
assert opts.engine == 'openai' and pipeline.supported()
pipeline.request_budget.configure(4)
active = peak = 0
lock = threading.Lock()
pdf_threads = []
batch_call = engine_guard.translate_batches
batch_barrier = threading.Barrier(2)

def observe_batch(*args, **kwargs):
    global active, peak
    with lock:
        active += 1
        peak = max(peak, active)
    try:
        batch_barrier.wait(timeout=30)  # Local parsing of the second PDF must run during this wait.
        return batch_call(*args, **kwargs)
    finally:
        with lock:
            active -= 1

def document(folder):
    pdf_threads.append(threading.get_ident())
    source = root / 'data' / 'qa-input' / folder / 'research-paper.pdf'
    result = translate_pdf(source, output_dir=str(root / 'data' / 'qa-pipeline' / folder), opts=opts,
        thread=2, cancel_event=threading.Event())
    pdf_threads.append(threading.get_ident())
    assert result.success, result.error
    with fitz.open(source) as original, fitz.open(result.files[0]['path']) as mono, \
            fitz.open(result.files[1]['path']) as dual:
        assert len(mono) == 3 and len(dual) == 6
        assert any('\u4e00' <= c <= '\u9fff' for c in mono[0].get_text())
        region = fitz.Rect(0, 425, 600, 800)
        assert original[0].get_pixmap(clip=region).samples == mono[0].get_pixmap(clip=region).samples
        assert original[1].get_pixmap().samples == mono[1].get_pixmap().samples
        for index in range(len(original)):
            assert original[index].get_pixmap().samples == dual[index * 2].get_pixmap().samples
    return {'folder': folder, 'elapsed': round(result.elapsed, 2), 'reference_pages': result.reference_pages}

with patch('app.pipeline.available_memory', return_value=8 * 1024**3), \
        patch('app.engine_guard.translate_batches', side_effect=observe_batch):
    results = pipeline.run_documents([lambda: document('folder-a'), lambda: document('folder-b')], 2)
assert peak == 2, f'Batch phases did not overlap: {peak}'
assert set(pdf_threads) == {threading.get_ident()}, 'PDF operations changed OS threads'
print(json.dumps({'documents': results, 'peak_batch_phases': peak,
    'pdf_os_threads': len(set(pdf_threads)), 'reference_and_original_pixels_identical': True}, indent=2))
