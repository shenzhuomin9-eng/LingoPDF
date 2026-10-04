import unittest
import fitz


def sample_pdf():
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_text((40, 70), 'Results and discussion', fontsize=16)
    page.insert_text((40, 100), 'The model improves scientific translation.', fontsize=11)
    page.insert_text((330, 390), 'References', fontsize=15)
    page.insert_text((330, 420), '[1] Smith. Original title. 2024.', fontsize=10)
    page.insert_text((40, 450), 'This left column is still body text.', fontsize=11)
    page = doc.new_page(width=600, height=800)
    page.insert_text((40, 70), '[2] Doe. Another original title. 2025.', fontsize=10)
    page = doc.new_page(width=600, height=800)
    page.insert_text((40, 70), 'Appendix A: Additional experiments', fontsize=15)
    page.insert_text((40, 100), 'This appendix should be translated.', fontsize=11)
    return doc.tobytes()


class ReferenceProtectionTests(unittest.TestCase):
    def test_reference_rule_is_not_drawn_twice_on_restoration(self):
        from app.references import prepare_pdf
        doc = fitz.open()
        page = doc.new_page(width=600, height=800)
        page.draw_line((40, 58.2), (550, 58.2), color=(0, 0, 0), width=0.4)
        page.insert_text((40, 90), 'References', fontsize=15)
        page.insert_text((40, 120), '[1] Original reference')
        page = doc.new_page(width=600, height=800)
        page.draw_line((40, 58.2), (550, 58.2), color=(0, 0, 0), width=0.4)
        page.insert_text((40, 100), '[2] Another original reference')
        source = doc.tobytes()
        plan = prepare_pdf(source)
        restored = fitz.open(stream=plan.restore(plan.stream), filetype='pdf')
        self.assertEqual(doc[1].get_pixmap().samples, restored[1].get_pixmap().samples)

    def test_author_year_references_continue_into_right_column(self):
        from app.references import prepare_pdf
        doc = fitz.open()
        page = doc.new_page(width=600, height=800)
        page.insert_text((40, 70), 'Body to translate')
        page.insert_text((40, 400), 'References', fontsize=15)
        page.insert_text((40, 430), 'Doe, J. Original research. 2024.', fontsize=10)
        page.insert_text((330, 70), 'Smith, A. More research. 2025.', fontsize=10)
        plan = prepare_pdf(doc.tobytes())
        text = fitz.open(stream=plan.stream, filetype='pdf')[0].get_text()
        self.assertIn('Body to translate', text)
        self.assertNotIn('More research', text)

    def test_reference_text_never_reaches_translation(self):
        from app.references import prepare_pdf
        plan = prepare_pdf(sample_pdf())
        doc = fitz.open(stream=plan.stream, filetype='pdf')
        self.assertIn('left column', doc[0].get_text())
        self.assertNotIn('Smith', doc[0].get_text())
        self.assertNotIn(1, plan.pages)
        self.assertIn(2, plan.pages)
        self.assertEqual(plan.reference_pages, 2)

    def test_restore_keeps_reference_region_and_bilingual_pages(self):
        from app.references import prepare_pdf
        source = sample_pdf()
        plan = prepare_pdf(source)
        mono = fitz.open(stream=plan.stream, filetype='pdf')
        mono[0].insert_text((40, 150), 'Translated body marker')
        restored = fitz.open(stream=plan.restore(mono.tobytes()), filetype='pdf')
        self.assertIn('Smith', restored[0].get_text())
        self.assertIn('Translated body marker', restored[0].get_text())
        original = fitz.open(stream=source, filetype='pdf')
        region = fitz.Rect(325, 375, 600, 800)
        self.assertEqual(original[0].get_pixmap(clip=region).samples,
                         restored[0].get_pixmap(clip=region).samples)
        dual = fitz.open()
        for i in range(len(original)):
            # pdf2zh uses the prepared (redacted) input for BOTH page variants.
            prepared = fitz.open(stream=plan.stream, filetype='pdf')
            dual.insert_pdf(prepared, from_page=i, to_page=i)
            dual.insert_pdf(mono, from_page=i, to_page=i)
        bilingual = fitz.open(stream=plan.restore(dual.tobytes(), dual=True), filetype='pdf')
        self.assertIn('Smith', bilingual[1].get_text())
        self.assertIn('Smith', bilingual[0].get_text())
        self.assertEqual(original[0].get_pixmap().samples, bilingual[0].get_pixmap().samples)

    def test_body_mention_is_not_a_reference_heading(self):
        from app.references import prepare_pdf
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((40, 80), 'We compare references across many studies.')
        plan = prepare_pdf(doc.tobytes())
        self.assertEqual(plan.reference_pages, 0)
        self.assertEqual(plan.pages, [0])

    def test_left_column_reference_continues_into_right(self):
        from app.references import prepare_pdf
        doc = fitz.open()
        page = doc.new_page(width=600, height=800)
        page.insert_text((40, 70), 'Body to translate', fontsize=14)
        page.insert_text((40, 400), '7. References', fontsize=15)
        page.insert_text((40, 430), '[1] Left reference. 2024.', fontsize=10)
        page.insert_text((330, 70), '[2] Right reference. 2025.', fontsize=10)
        plan = prepare_pdf(doc.tobytes())
        text = fitz.open(stream=plan.stream, filetype='pdf')[0].get_text()
        self.assertIn('Body to translate', text)
        self.assertNotIn('Left reference', text)
        self.assertNotIn('Right reference', text)

    def test_reference_continuation_ends_at_right_column_appendix(self):
        from app.references import prepare_pdf
        doc = fitz.open()
        page = doc.new_page(width=600, height=800)
        page.insert_text((40, 70), 'References', fontsize=15)
        page.insert_text((40, 100), '[1] Reference first. 2024.')
        page = doc.new_page(width=600, height=800)
        page.insert_text((40, 100), '[2] Left reference upper. 2024.')
        page.insert_text((40, 450), '[3] Left reference lower. 2025.')
        page.insert_text((330, 70), 'Appendix A', fontsize=15)
        page.insert_text((330, 100), 'Body in appendix.')
        plan = prepare_pdf(doc.tobytes())
        text = fitz.open(stream=plan.stream, filetype='pdf')[1].get_text()
        self.assertNotIn('Left reference', text)
        self.assertIn('Body in appendix', text)

    def test_rotated_reference_region_is_protected_and_restored(self):
        from app.references import prepare_pdf
        doc = fitz.open()
        page = doc.new_page(width=600, height=800)
        page.insert_text((40, 70), 'Body text')
        page.insert_text((40, 400), 'References', fontsize=15)
        page.insert_text((40, 700), '[1] Reference near page bottom. 2025.')
        page.set_rotation(90)
        source = doc.tobytes()
        plan = prepare_pdf(source)
        self.assertNotIn('page bottom', fitz.open(stream=plan.stream, filetype='pdf')[0].get_text())
        restored = fitz.open(stream=plan.restore(plan.stream), filetype='pdf')
        self.assertEqual(restored[0].rotation, 90)
        self.assertEqual(doc[0].get_pixmap().samples, restored[0].get_pixmap().samples)


if __name__ == '__main__':
    unittest.main()
