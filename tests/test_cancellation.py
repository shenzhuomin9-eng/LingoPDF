import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from app.jobs import JobManager
from app.translator import TranslateOptions, TranslateResult


class CancellationLifecycleTests(unittest.TestCase):
    def test_queued_cancel_does_not_wait_for_another_job(self):
        manager = JobManager()
        manager._execution_lock.acquire()
        try:
            job = manager.create_job([('a.pdf', Path('data/qa-cancel/queued/0/a.pdf'), 1)], TranslateOptions(), 4)
            manager.cancel(job.id)
            manager._threads[-1].join(1)
            self.assertEqual(job.status, 'canceled')
            self.assertTrue(Path('data/qa-cancel/queued/job.json').exists())
        finally:
            manager._execution_lock.release()

    def test_cancel_is_not_terminal_until_worker_acknowledges(self):
        started, release = threading.Event(), threading.Event()
        def translate(*args, **kwargs):
            started.set()
            release.wait(3)
            return TranslateResult(canceled=True, error='Canceled')
        manager = JobManager()
        with patch('app.jobs.translate_pdf', side_effect=translate):
            job = manager.create_job([('a.pdf', Path('data/qa-cancel/job/0/a.pdf'), 1),
                                      ('b.pdf', Path('data/qa-cancel/job/1/b.pdf'), 1)],
                                     TranslateOptions(), 4)
            self.assertTrue(started.wait(3))
            self.assertTrue(manager.cancel(job.id))
            try:
                self.assertEqual(job.status, 'canceling')
                self.assertTrue(job.cancel_event.is_set())
            finally:
                release.set()
            manager._threads[-1].join(4)
            self.assertEqual(job.status, 'canceled')
            self.assertTrue(all(f.status == 'canceled' for f in job.files))


if __name__ == '__main__':
    unittest.main()
