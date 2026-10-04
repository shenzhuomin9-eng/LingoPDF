"""Verify the outputs produced through the real browser flow."""
import json
from pathlib import Path
import fitz

root = Path(__file__).resolve().parents[1]
qa = root / 'data' / 'qa-input'
evidence = root / 'docs' / 'verification'
evidence.mkdir(parents=True, exist_ok=True)
summary = []
for folder in ('folder-a', 'folder-b'):
    original_path = qa / folder / 'research-paper.pdf'
    output_path = max((qa / folder / 'LingoPDF').glob('research-paper_zh*.pdf'), key=lambda p: p.stat().st_mtime)
    dual_path = max((qa / folder / 'LingoPDF').glob('research-paper_dual*.pdf'), key=lambda p: p.stat().st_mtime)
    with fitz.open(original_path) as original, fitz.open(output_path) as output, fitz.open(dual_path) as dual:
        assert len(output) == 3 and len(dual) == 6
        text = output[0].get_text()
        assert any('\u4e00' <= char <= '\u9fff' for char in text), 'Body was not translated'
        assert 'Smith, J. Scientific document translation.' in text
        assert 'Brown, C. Preserving equations' in output[1].get_text()
        assert any('\u4e00' <= char <= '\u9fff' for char in output[2].get_text()), 'Appendix not translated'
        rect = fitz.Rect(0, 425, 600, 800)
        assert original[0].get_pixmap(clip=rect).samples == output[0].get_pixmap(clip=rect).samples, 'References changed visually'
        assert original[1].get_pixmap().samples == output[1].get_pixmap().samples
        assert original[0].get_pixmap(clip=rect).samples == dual[1].get_pixmap(clip=rect).samples
        for index in range(len(original)):
            assert original[index].get_pixmap().samples == dual[index * 2].get_pixmap().samples, 'Bilingual original page changed'
        if folder == 'folder-a':
            output[0].get_pixmap(matrix=fitz.Matrix(1.25,1.25)).save(evidence / 'translated-paper.png')
        summary.append({'folder':folder,'mono_pages':len(output),'dual_pages':len(dual),'references_pixel_identical':True,
                        'bilingual_originals_pixel_identical':True,'output':str(output_path)})
print(json.dumps(summary, indent=2))
