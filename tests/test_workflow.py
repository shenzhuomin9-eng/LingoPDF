import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz
from fastapi.testclient import TestClient
from app import config as cfg
from app.main import app
from app.jobs import Job, JobFile
from app.translator import TranslateOptions


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config_patch = patch.multiple(cfg, CONFIG_DIR=self.root,
                                          CONFIG_FILE=self.root / 'config.json')
        self.config_patch.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.config_patch.stop()
        self.tmp.cleanup()

    def make_pdf(self, name='paper.pdf'):
        path = self.root / name
        doc = fitz.open()
        doc.new_page().insert_text((40, 80), 'A scientific translation test.')
        doc.save(path)
        return path

    def test_short_keys_are_always_masked(self):
        for key in ('abc', 'abcd', 'abcdefgh'):
            self.assertNotEqual(cfg.masked({'api_key': key})['api_key'], key)

    def test_local_import_retains_verified_source(self):
        path = self.make_pdf()
        response = self.client.post('/api/local-files', json={'paths': [str(path)]})
        self.assertEqual(response.status_code, 200, response.text)
        item = response.json()['files'][0]
        self.assertEqual(item['source_path'], str(path.resolve()))
        self.assertIn('id', item)

    def test_bad_import_and_config_are_rejected(self):
        self.assertEqual(self.client.post('/api/local-files', json={'paths': ['missing.pdf']}).status_code, 400)
        self.assertEqual(self.client.post('/api/config', json={'thread': 0}).status_code, 422)
        self.assertEqual(self.client.post('/api/config', json={'lang_out': 'bad'}).status_code, 422)

    def test_duplicate_upload_names_are_isolated(self):
        data = self.make_pdf().read_bytes()
        with patch('app.jobs.JobManager._run'):
            r = self.client.post('/api/translate', files=[('files', ('same.pdf', data, 'application/pdf')),
                                                        ('files', ('same.pdf', data, 'application/pdf'))])
        self.assertEqual(r.status_code, 200, r.text)
        from app.jobs import manager
        job = manager.get(r.json()['job_id'])
        self.assertNotEqual(job.files[0].upload_path, job.files[1].upload_path)

    def test_export_next_to_original_without_overwrite(self):
        source = self.make_pdf()
        output = self.root / 'translated.pdf'
        output.write_bytes(source.read_bytes())
        jf = JobFile(name=source.name, upload_path=source, size=source.stat().st_size,
                     source_path=source, status='done', outputs=[{'name': 'paper_zh.pdf', 'path': str(output)}])
        job = Job(id='testexport', files=[jf], opts=TranslateOptions(), thread=4)
        from app.storage import save_outputs
        first = save_outputs(job)
        self.assertEqual(Path(first['saved'][0]['path']).parent, source.parent / 'LingoPDF')
        saved = Path(first['saved'][0]['path'])
        saved.write_bytes(b'existing user result')
        second = save_outputs(job)
        self.assertNotEqual(first['saved'][0]['path'], second['saved'][0]['path'])
        self.assertEqual(saved.read_bytes(), b'existing user result')

    def test_cancel_reaches_active_engine(self):
        from app.jobs import JobManager
        manager = JobManager()
        job = Job(id='canceltest', files=[], opts=TranslateOptions(), thread=4)
        manager._jobs[job.id] = job
        self.assertTrue(manager.cancel(job.id))
        self.assertTrue(job.cancel_event.is_set())


if __name__ == '__main__':
    unittest.main()
