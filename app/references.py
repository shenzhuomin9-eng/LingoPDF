"""Keep bibliography text out of provider requests and restore pristine PDF regions."""
from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass
import fitz

_HEADING = re.compile(
    r"^(?:(?:\d+(?:\.\d+)*|[ivx]+)\s*[.)、:]?\s*)?"
    r"(?:references|bibliography|literature cited|works cited|reference list|"
    r"参考文献|參考文獻|参考资料|参考文獻|文献|références|referencias|literaturverzeichnis)\s*[:：.]?$", re.I)
_END = re.compile(r"^(?:(?:\d+(?:\.\d+)*|[ivx]+)\s*[.)]?\s*)?"
                  r"(?:appendi[xc](?:es)?\b|supplementary\b|acknowledg(?:e)?ments\b|附录|附錄|致谢)", re.I)


def _lines(page):
    result = []
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            text = ''.join(s['text'] for s in line['spans']).strip()
            if text:
                result.append((unicodedata.normalize('NFKC', text), fitz.Rect(line['bbox'])))
    return result


@dataclass
class ReferencePlan:
    original: bytes
    stream: bytes
    pages: list[int]
    regions: dict[int, list[fitz.Rect]]
    rotations: list[int]

    @property
    def reference_pages(self):
        return len(self.regions)

    def restore(self, translated: bytes, dual: bool = False) -> bytes:
        if not self.regions and not any(self.rotations):
            return translated
        with fitz.open(stream=self.original, filetype='pdf') as original, \
                fitz.open(stream=translated, filetype='pdf') as result:
            if len(result) != len(original) * (2 if dual else 1):
                raise ValueError('Translated page count changed; cannot safely restore references')
            for index in range(len(original)):
                source = original[index]
                source.set_rotation(0)
                target = result[index * 2 + 1 if dual else index]
                target.set_rotation(0)
                for rect in self.regions.get(index, []):
                    # Engine input keeps graphics. Clear the protected region
                    # before copying it, so rules and images are drawn once.
                    target.draw_rect(rect, color=None, fill=(1, 1, 1), overlay=True)
                    target.show_pdf_page(rect, original, index, clip=rect, overlay=True)
                source.set_rotation(self.rotations[index])
                target.set_rotation(self.rotations[index])
            if dual:
                # Both halves were built from the redacted engine input. Replace
                # every original half with the pristine page, including annotations.
                for index in range(len(original)):
                    result.delete_page(index * 2)
                    result.insert_pdf(original, from_page=index, to_page=index, start_at=index * 2)
            return result.tobytes(garbage=3, deflate=True)


def _protected_regions(page, lines, heading, active):
    """Use column reading order, not just Y, for bibliography/appendix boundaries."""
    width, height = page.rect.width, page.rect.height
    mid = width / 2
    columns = any(rect.x0 >= mid and rect.x1 > mid + 30 for _, rect in lines)
    full_heading = heading is not None and heading.x1 >= mid and heading.x0 < mid
    # A short heading can also start a full-width section beneath two body columns.
    if columns and heading is not None and heading.x0 < mid:
        above_right = [text for text, rect in lines if rect.x0 >= mid and rect.y0 < heading.y0]
        reference_evidence = r'^\s*(?:\[\d+\]|\d+[.)])|\b(?:18|19|20)\d{2}\b|^[A-Z][\w\s\x27-]+,\s*[A-Z]\.'
        if above_right and not any(re.search(reference_evidence, text) for text in above_right):
            full_heading = True
    columns = columns and not full_heading
    start_col = int(heading.x0 >= mid) if heading is not None and columns else 0
    start_y = max(0, heading.y0 - 1) if heading is not None else 0
    def key(rect):
        return (int(rect.x0 >= mid) if columns else 0, rect.y0)
    end_candidates = [rect for text, rect in lines if _END.match(text)
                      and (active or key(rect) > (start_col, start_y))]
    end = min(end_candidates, key=key) if end_candidates else None
    if not columns:
        end_y = max(start_y, end.y0 - 1) if end else height
        rects = [fitz.Rect(0, start_y, width, end_y)]
    else:
        end_col = int(end.x0 >= mid) if end else 1
        rects = []
        for col in range(start_col, end_col + 1):
            y0 = start_y if col == start_col else 0
            y1 = end.y0 - 1 if end and col == end_col else height
            if y1 > y0:
                rects.append(fitz.Rect(mid * col, y0, mid * (col + 1), y1))
    rects = [rect for rect in rects if not rect.is_empty and any(rect.intersects(line) for _, line in lines)]
    return rects, end is None


def prepare_pdf(stream: bytes, enabled: bool = True) -> ReferencePlan:
    """Protect standalone bibliography sections; resume at appendix/acknowledgments.

    Normalize rotation before processing because PDF text coordinates are unrotated.
    Bibliography regions are physically removed from the input seen by the engine.
    """
    regions, pages, rotations = {}, [], []
    active = False
    with fitz.open(stream=stream, filetype='pdf') as doc:
        if doc.needs_pass:
            raise ValueError('PDF is password protected; unlock it before translation')
        for index, page in enumerate(doc):
            rotations.append(page.rotation)
            page.set_rotation(0)
            lines = _lines(page)
            headings = [rect for text, rect in lines if _HEADING.fullmatch(text)]
            rects = []
            if enabled and (active or headings):
                heading = None if active else min(headings, key=lambda r: (r.y0, r.x0))
                rects, active = _protected_regions(page, lines, heading, active)
            if rects:
                regions[index] = rects
                for rect in rects:
                    page.add_redact_annot(rect, fill=None, cross_out=False)
                page.apply_redactions(images=0, graphics=0, text=0)
            if page.get_text().strip():
                pages.append(index)
        prepared = doc.tobytes(garbage=3, deflate=True) if regions or any(rotations) else stream
    return ReferencePlan(stream, prepared, pages, regions, rotations)
