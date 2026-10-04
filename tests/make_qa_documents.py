"""Generate disposable input documents for real browser and PDF verification."""
from pathlib import Path
import fitz

root = Path(__file__).resolve().parents[1] / 'data' / 'qa-input'
root.mkdir(parents=True, exist_ok=True)
for folder in ('folder-a', 'folder-b'):
    target = root / folder
    target.mkdir(exist_ok=True)
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_text((45, 60), 'Scientific Translation Study', fontsize=20)
    page.insert_text((45, 105), 'Abstract', fontsize=15)
    page.insert_textbox(fitz.Rect(45,125,555,240),
        'This study evaluates the accuracy and efficiency of scientific document translation. '
        'Our method preserves mathematical equations and the original document layout. '
        'The experimental results demonstrate a significant improvement in reading comprehension.', fontsize=12)
    page.insert_text((45, 265), 'Results and discussion', fontsize=15)
    page.insert_textbox(fitz.Rect(45,285,555,375),
        'The proposed model reduces translation latency while maintaining consistent terminology. '
        'Users can compare the original text with the translated document. '
        'The source file remains unchanged after processing.', fontsize=12)
    page.insert_text((45, 440), 'References', fontsize=15)
    page.insert_text((45, 470), '[1] Smith, J. Scientific document translation. Journal of Research, 2024.', fontsize=10)
    page.insert_text((45, 490), '[2] Doe, A. Consistent terminology in language models. 2025.', fontsize=10)
    page = doc.new_page(width=600, height=800)
    page.insert_text((45, 70), '[3] Brown, C. Preserving equations in digital documents. 2023.', fontsize=10)
    page = doc.new_page(width=600, height=800)
    page.insert_text((45, 70), 'Appendix A: Additional experiments', fontsize=15)
    page.insert_text((45, 110), 'The additional experiments confirm the robustness of the method.', fontsize=12)
    doc.save(target / 'research-paper.pdf')
doc = fitz.open()
page = doc.new_page()
page.insert_text((40,80), 'References', fontsize=16)
page.insert_text((40,110), '[1] Original bibliography entry. 2024.', fontsize=11)
doc.save(root / 'references-only.pdf')
(root / 'broken.pdf').write_bytes(b'not a valid PDF')
print(root)
