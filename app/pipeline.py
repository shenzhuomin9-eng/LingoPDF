"""Cooperative document pipeline: one PDF thread, bounded network overlap."""
from __future__ import annotations
import asyncio
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import dataclass
from functools import wraps

pdf_lock = threading.RLock()
_scheduler = ContextVar('document_scheduler', default=None)


def serialized_pdf(call):
    @wraps(call)
    def wrapped(*args, **kwargs):
        with pdf_lock:
            return call(*args, **kwargs)
    return wrapped


def available_memory():
    try:
        import psutil
        return psutil.virtual_memory().available
    except ImportError:
        if __import__('sys').platform == 'win32':
            import ctypes
            class Memory(ctypes.Structure):
                _fields_ = [('length', ctypes.c_uint32), ('load', ctypes.c_uint32)] + [
                    (name, ctypes.c_uint64) for name in ('total', 'available', 'page_total',
                        'page_available', 'virtual_total', 'virtual_available', 'extended')]
            state = Memory()
            state.length = ctypes.sizeof(state)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
                return state.available
        return 0  # Unknown resources: stay serial.


def supported():
    try:
        import greenlet
        from pdf2zh.converter import TranslateConverter
        return hasattr(TranslateConverter, 'flush_all')
    except ImportError:
        return False


class RequestBudget:
    def __init__(self, limit=4):
        self.limit = max(1, limit)
        self.active = 0
        self.condition = threading.Condition()

    def configure(self, limit):
        with self.condition:
            self.limit = max(1, limit)
            self.condition.notify_all()

    @contextmanager
    def slot(self, cancel_event):
        with self.condition:
            while self.active >= self.limit:
                if cancel_event and cancel_event.is_set():
                    raise asyncio.CancelledError('Translation canceled')
                self.condition.wait(0.1)
            if cancel_event and cancel_event.is_set():
                raise asyncio.CancelledError('Translation canceled')
            self.active += 1
        try:
            yield
        finally:
            with self.condition:
                self.active -= 1
                self.condition.notify_all()


request_budget = RequestBudget()


@dataclass
class _Waiting:
    future: object


@dataclass
class _Outcome:
    value: object = None
    error: BaseException | None = None


def network_wait(call):
    scheduler = _scheduler.get()
    if scheduler is None:
        return call()
    packet = scheduler.root.switch(_Waiting(scheduler.pool.submit(call)))
    if packet.error:
        raise packet.error
    return packet.value


def run_documents(calls, max_active=2):
    """All document functions execute on this same OS thread, even after waits."""
    if max_active <= 1:
        with pdf_lock:
            return [call() for call in calls]
    try:
        from greenlet import greenlet, getcurrent
    except ImportError:
        with pdf_lock:
            return [call() for call in calls]
    from types import SimpleNamespace
    scheduler = SimpleNamespace(root=getcurrent(), pool=ThreadPoolExecutor(max_workers=max_active))
    pending, outcomes, next_index = {}, [None] * len(calls), 0
    def entry(call):
        token = _scheduler.set(scheduler)
        try:
            return _Outcome(value=call())
        except BaseException as error:
            return _Outcome(error=error)
        finally:
            _scheduler.reset(token)
    def resume(fiber, index, packet=None):
        message = fiber.switch(packet) if packet is not None else fiber.switch()
        if fiber.dead:
            outcomes[index] = message
        else:
            pending[fiber] = (index, message.future)
    try:
        # PyMuPDF work never enters a network worker or overlaps other PDF work.
        with pdf_lock:
            while next_index < len(calls) or pending:
                limit = max_active if available_memory() >= 2 * 1024**3 else 1
                while next_index < len(calls) and len(pending) < limit:
                    index = next_index
                    next_index += 1
                    resume(greenlet(lambda call=calls[index]: entry(call)), index)
                if pending:
                    ready, _ = wait([future for _, future in pending.values()], timeout=0.1,
                                    return_when=FIRST_COMPLETED)
                    for fiber, (index, future) in list(pending.items()):
                        if future in ready:
                            del pending[fiber]
                            try:
                                packet = _Outcome(value=future.result())
                            except BaseException as error:
                                packet = _Outcome(error=error)
                            resume(fiber, index, packet)
    finally:
        scheduler.pool.shutdown(wait=True)
    for outcome in outcomes:
        if outcome.error:
            raise outcome.error
    return [outcome.value for outcome in outcomes]
