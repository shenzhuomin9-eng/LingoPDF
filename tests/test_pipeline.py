import threading
import time
import unittest
from unittest.mock import patch


class DocumentPipelineTests(unittest.TestCase):
    def test_job_starts_two_documents_with_existing_total_request_budget(self):
        from app.jobs import JobManager
        from app.translator import TranslateOptions, TranslateResult
        from app.pipeline import network_wait
        from pathlib import Path
        import tempfile
        active, peak = 0, 0
        lock = threading.Lock()
        def translate(*args, **kwargs):
            def network():
                nonlocal active, peak
                with lock:
                    active += 1
                    peak = max(peak, active)
                time.sleep(0.05)
                with lock:
                    active -= 1
            network_wait(network)
            return TranslateResult(files=[{'name':'out.pdf','path':'not-needed'}])
        with tempfile.TemporaryDirectory() as temp, patch('app.jobs.translate_pdf', side_effect=translate), \
                patch('app.pipeline.supported', return_value=True), \
                patch('app.pipeline.available_memory', return_value=8 * 1024**3):
            root = Path(temp)
            manager = JobManager(history_dir=root)
            job = manager.create_job([('a.pdf', root/'job'/'0'/'a.pdf', 100),
                                      ('b.pdf', root/'job'/'1'/'b.pdf', 100)], TranslateOptions(engine='openai'), 4)
            manager._threads[-1].join(4)
            self.assertEqual(job.status, 'finished')
            self.assertEqual(peak, 2)
            self.assertEqual(job.document_parallel, 2)

    def test_network_waits_overlap_but_pdf_stages_share_one_thread(self):
        from app.pipeline import run_documents, network_wait
        local_threads, active, peak = [], 0, 0
        lock = threading.Lock()
        def network():
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.1)
            with lock:
                active -= 1
            return 'translated'
        def document():
            local_threads.append(threading.get_ident())
            text = network_wait(network)
            local_threads.append(threading.get_ident())
            return text
        with patch('app.pipeline.available_memory', return_value=8 * 1024**3):
            results = run_documents([document] * 4, max_active=2)
        self.assertEqual(results, ['translated'] * 4)
        self.assertEqual(peak, 2)
        self.assertEqual(set(local_threads), {threading.get_ident()})

    def test_memory_pressure_reverts_to_one_document(self):
        from app.pipeline import run_documents, network_wait
        active, peak = 0, 0
        def network():
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            time.sleep(0.02)
            active -= 1
        with patch('app.pipeline.available_memory', return_value=512 * 1024**2):
            run_documents([lambda: network_wait(network)] * 3, max_active=2)
        self.assertEqual(peak, 1)

    def test_provider_budget_caps_requests_across_documents(self):
        from app.pipeline import RequestBudget
        from concurrent.futures import ThreadPoolExecutor
        budget = RequestBudget(2)
        active, peak = 0, 0
        lock = threading.Lock()
        def request(_):
            nonlocal active, peak
            with budget.slot(None):
                with lock:
                    active += 1
                    peak = max(peak, active)
                time.sleep(0.02)
                with lock:
                    active -= 1
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(request, range(8)))
        self.assertEqual(peak, 2)


if __name__ == '__main__':
    unittest.main()
