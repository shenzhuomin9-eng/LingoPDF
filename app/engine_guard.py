"""Application-owned API quality and cancellation guards; no site-package edits."""
from __future__ import annotations
import asyncio
import re
import threading
from collections import Counter
from contextvars import ContextVar

translation_cancel = ContextVar('translation_cancel', default=None)
_installed = False
_lock = threading.Lock()


def check_canceled(event):
    if event is not None and event.is_set():
        raise asyncio.CancelledError('Translation canceled')


def cancellable_request(create, event, *args, **kwargs):
    """Discard an in-flight response on cancel; the worker cannot mutate job state."""
    check_canceled(event)
    if event is None:
        return create(*args, **kwargs)
    completed = threading.Event()
    outcome = {}
    def request():
        try:
            outcome['result'] = create(*args, **kwargs)
        except BaseException as error:
            outcome['error'] = error
        finally:
            completed.set()
    threading.Thread(target=request, daemon=True, name='lingopdf-provider').start()
    while not completed.wait(0.1):
        check_canceled(event)
    check_canceled(event)
    if 'error' in outcome:
        raise outcome['error']
    return outcome['result']


def valid_placeholders(source, translated):
    pattern = r'\{+v\d+\}+'
    return Counter(re.findall(pattern, source)) == Counter(re.findall(pattern, translated))


def cached_translation(engine, text):
    for cache in (engine.cache, getattr(engine, 'legacy_cache', None)):
        if cache is None:
            continue
        result = cache.get(text)
        if result and valid_placeholders(text, result):
            if cache is not engine.cache:
                engine.cache.set(text, result)
            return result
    return None


def translate_batches(engine, texts, workers=4, progress_cb=None):
    """Cache and batch paragraphs without silently replacing failures with source text."""
    check_canceled(engine.cancel_event)
    results, batches, group, characters = [None] * len(texts), [], [], 0
    for index, text in enumerate(texts):
        if not text.strip() or re.fullmatch(r'\{+v\d+\}+', text.strip()):
            results[index] = text
            continue
        cached = None if engine.ignore_cache else cached_translation(engine, text)
        if cached:
            results[index] = cached
            continue
        if group and (len(group) >= 12 or characters + len(text) > 3500):
            batches.append(group)
            group, characters = [], 0
        group.append(index)
        characters += len(text)
    if group:
        batches.append(group)
    completed, progress_lock = 0, threading.Lock()
    def translate_group(indices):
        nonlocal completed
        check_canceled(engine.cancel_event)
        numbered = '\n'.join(f'[[{i}]] {texts[index]}' for i, index in enumerate(indices))
        response = engine.client.chat.completions.create(model=engine.model, **engine.options,
            messages=[{'role': 'user', 'content': engine._batch_prompt(numbered, len(indices))}], timeout=120)
        if not response.choices or not response.choices[0].message.content:
            raise ValueError('Translation service returned empty text')
        content = engine.think_filter_regex.sub('', response.choices[0].message.content).strip()
        pairs = re.findall(r'\[\[(\d+)\]\]\s*(.*?)(?=\[\[\d+\]\]|\Z)', content, re.DOTALL)
        mapping = {int(key): value.strip() for key, value in pairs}
        markers_valid = len(pairs) == len(mapping) and set(mapping) <= set(range(len(indices)))
        for marker, index in enumerate(indices):
            check_canceled(engine.cancel_event)
            translated = mapping.get(marker) if markers_valid else None
            if not translated or not valid_placeholders(texts[index], translated):
                translated = engine.translate(texts[index], True)
            if not translated:
                raise ValueError('Translation service returned empty text')
            engine.cache.set(texts[index], translated)
            results[index] = translated
        with progress_lock:
            completed += 1
            if progress_cb:
                progress_cb(completed / max(1, len(batches)))
    if len(batches) > 1 and workers > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(workers, len(batches))) as pool:
            list(pool.map(translate_group, batches))
    else:
        for batch in batches:
            translate_group(batch)
    check_canceled(engine.cancel_event)
    return results


def install_api_guard():
    global _installed
    with _lock:
        if _installed:
            return
        import pdf2zh.converter as converter
        import pdf2zh.translator as translators
        original = translators.OpenAITranslator

        class GuardedOpenAITranslator(original):
            def __init__(self, *args, **kwargs):
                self.cancel_event = translation_cancel.get()
                super().__init__(*args, **kwargs)
                # Avoid unbounded provider retries and capture cancellation on each request.
                self.client.max_retries = 1
                create = self.client.chat.completions.create
                from .pipeline import request_budget
                def bounded_create(*args, **kwargs):
                    with request_budget.slot(self.cancel_event):
                        return create(*args, **kwargs)
                def guarded_create(*args, **kwargs):
                    check_canceled(self.cancel_event)
                    kwargs['timeout'] = min(float(kwargs.get('timeout') or 90), 180)
                    result = cancellable_request(bounded_create, self.cancel_event, *args, **kwargs)
                    check_canceled(self.cancel_event)
                    return result
                self.client.chat.completions.create = guarded_create
                self.add_cache_impact_parameters('lingopdf_quality_guard', 2)
                # The previous academic prompt differs only in its overly strict
                # token-order rule. Reuse compatible results after ID/count validation.
                from copy import deepcopy
                from pdf2zh.cache import TranslationCache
                params = deepcopy(self.cache.params)
                for message in params.get('prompt', []):
                    message['content'] = message['content'].replace(
                        'Preserve every formula placeholder such as {v0} exactly, with the same identifier and count.\n'
                        'Placeholders may move with natural target-language sentence structure; never drop or duplicate them.',
                        'Preserve every formula placeholder such as {v0} exactly, in its original order and count.')
                self.legacy_cache = TranslationCache(self.name, params)

            def do_translate(self, text):
                response = self.client.chat.completions.create(model=self.model, **self.options,
                                                               messages=self.prompt(text, self.prompttext))
                if not response.choices or not response.choices[0].message.content:
                    raise ValueError('Translation service returned empty text')
                content = response.choices[0].message.content.strip()
                return self.think_filter_regex.sub('', content).strip()

            def translate(self, text, ignore_cache=False):
                check_canceled(self.cancel_event)
                if not (ignore_cache or self.ignore_cache):
                    cached = cached_translation(self, text)
                    if cached is not None:
                        return cached
                result = super().translate(text, True)
                if not valid_placeholders(text, result):
                    result = super().translate(text, True)
                    if not valid_placeholders(text, result):
                        raise ValueError('Formula placeholders changed; refusing an incorrect translation')
                return result

            def batch_translate(self, texts, workers=4, progress_cb=None):
                from .pipeline import network_wait
                return network_wait(lambda: translate_batches(self, texts, workers, progress_cb))

            def _batch_prompt(self, numbered, seg_count=0):
                # Installed batch-capable engines use the same academic rules as single paragraphs.
                rules = self.prompt(numbered, self.prompttext)[0]['content']
                return (f'There are exactly {seg_count} numbered segments. Keep [[n]] markers. '
                        'Translate every segment separately, in order. Do not merge or omit segments. '
                        'Return only the numbered translations.\n' + rules)

        translators.OpenAITranslator = GuardedOpenAITranslator
        converter.OpenAITranslator = GuardedOpenAITranslator
        _installed = True
