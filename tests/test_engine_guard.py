import asyncio
import threading
import unittest


class EngineGuardTests(unittest.TestCase):
    def test_compatible_cached_translation_with_reordered_formulas_needs_no_request(self):
        from app.engine_guard import translate_batches
        from types import SimpleNamespace
        stored = {}
        engine = SimpleNamespace(cancel_event=None, ignore_cache=False,
            cache=SimpleNamespace(get=stored.get, set=lambda text, result: stored.update({text: result})),
            legacy_cache=SimpleNamespace(get=lambda text: '先 {v1}，再 {v0}'))
        self.assertEqual(translate_batches(engine, ['First {v0}, then {v1}']), ['先 {v1}，再 {v0}'])
        self.assertIn('First {v0}, then {v1}', stored)

    def test_batch_mapping_preserves_formulas_and_reports_progress(self):
        from app.engine_guard import translate_batches
        from types import SimpleNamespace
        import re
        cache = {}
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='[[0]] 公式 {{v0}}\n[[1]] 结果'))])
        engine = SimpleNamespace(cancel_event=None, ignore_cache=False,
            cache=SimpleNamespace(get=cache.get, set=lambda text, result: cache.update({text: result})),
            client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response))),
            model='test', options={}, _batch_prompt=lambda *args: 'prompt', think_filter_regex=re.compile(r'^<think>.*?</think>', re.S))
        progress = []
        result = translate_batches(engine, ['Equation {{v0}}', 'Results'], progress_cb=progress.append)
        self.assertEqual(result, ['公式 {{v0}}', '结果'])
        self.assertEqual(progress, [1.0])
        self.assertEqual(cache['Results'], '结果')

    def test_provider_failure_cannot_be_reported_as_successful_source_text(self):
        from app.engine_guard import translate_batches
        from types import SimpleNamespace
        class Cache:
            def get(self, text): return None
            def set(self, text, translated): pass
        def unavailable(*args, **kwargs):
            raise OSError('Provider unavailable')
        engine = SimpleNamespace(cancel_event=None, ignore_cache=False, cache=Cache(),
            client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=unavailable))),
            model='test', options={}, _batch_prompt=lambda *args: 'prompt', translate=unavailable)
        with self.assertRaises(OSError):
            translate_batches(engine, ['A sentence which must be translated.'])

    def test_pending_provider_response_does_not_delay_cancel(self):
        from app.engine_guard import cancellable_request
        cancel, entered, release = threading.Event(), threading.Event(), threading.Event()
        def slow_provider():
            entered.set()
            release.wait(3)
            return 'late response'
        threading.Timer(0.05, cancel.set).start()
        try:
            with self.assertRaises(asyncio.CancelledError):
                cancellable_request(slow_provider, cancel)
            self.assertTrue(entered.is_set())
            self.assertFalse(release.is_set())
        finally:
            release.set()

    def test_formula_tokens_cannot_be_dropped_or_duplicated(self):
        from app.engine_guard import valid_placeholders
        self.assertTrue(valid_placeholders('Equation {{v0}} and {v1}', '公式 {{v0}} 与 {v1}'))
        self.assertFalse(valid_placeholders('Equation {v0}', '公式'))
        self.assertFalse(valid_placeholders('Equation {v0}', '公式 {v0} {v0}'))
        # Chinese syntax may legitimately move an equation within a sentence.
        self.assertTrue(valid_placeholders('{v0} then {v1}', '{v1} 然后 {v0}'))
        self.assertFalse(valid_placeholders('{v0} then {v1}', '{v0} 然后 {v2}'))

    def test_context_cancellation_captured_per_engine_instance(self):
        from app.engine_guard import check_canceled
        event = threading.Event()
        check_canceled(event)
        event.set()
        with self.assertRaises(asyncio.CancelledError):
            check_canceled(event)


if __name__ == '__main__':
    unittest.main()
