"""Native file picker, isolated from the web server's event loop."""
import json
import sys
from pathlib import Path


def windows_picker():
    import ctypes
    from ctypes import wintypes as w
    class OpenFileName(ctypes.Structure):
        _fields_ = [('lStructSize',w.DWORD),('hwndOwner',w.HWND),('hInstance',w.HINSTANCE),
                    ('lpstrFilter',w.LPCWSTR),('lpstrCustomFilter',w.LPWSTR),('nMaxCustFilter',w.DWORD),
                    ('nFilterIndex',w.DWORD),('lpstrFile',w.LPWSTR),('nMaxFile',w.DWORD),
                    ('lpstrFileTitle',w.LPWSTR),('nMaxFileTitle',w.DWORD),('lpstrInitialDir',w.LPCWSTR),
                    ('lpstrTitle',w.LPCWSTR),('Flags',w.DWORD),('nFileOffset',w.WORD),('nFileExtension',w.WORD),
                    ('lpstrDefExt',w.LPCWSTR),('lCustData',w.LPARAM),('lpfnHook',ctypes.c_void_p),
                    ('lpTemplateName',w.LPCWSTR),('pvReserved',ctypes.c_void_p),('dwReserved',w.DWORD),('FlagsEx',w.DWORD)]
    buffer = ctypes.create_unicode_buffer(65536)
    data = OpenFileName()
    data.lStructSize = ctypes.sizeof(data)
    data.lpstrFilter = 'Documents\0*.pdf;*.docx;*.pptx;*.doc;*.ppt\0\0'
    data.lpstrFile = ctypes.cast(buffer, w.LPWSTR)
    data.nMaxFile = len(buffer)
    data.lpstrTitle = 'LingoPDF - Select source documents'
    # No browser owner is available in this separate process. Watch this GUI
    # thread briefly and raise its visible picker. An OFN hook would downgrade
    # Windows' modern file chooser to the legacy dialog.
    import threading
    import time
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    user32.SetWindowPos.argtypes = [w.HWND, w.HWND, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, w.UINT]
    user32.SetWindowPos.restype = w.BOOL
    user32.SetForegroundWindow.argtypes = [w.HWND]
    user32.SetForegroundWindow.restype = w.BOOL
    user32.IsWindowVisible.argtypes = [w.HWND]
    user32.IsWindowVisible.restype = w.BOOL
    user32.GetWindowTextW.argtypes = [w.HWND, w.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    enum_type = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    user32.EnumThreadWindows.argtypes = [w.DWORD, enum_type, w.LPARAM]
    user32.EnumThreadWindows.restype = w.BOOL
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.GetCurrentThreadId.restype = w.DWORD
    gui_thread = kernel32.GetCurrentThreadId()
    closed = threading.Event()
    @enum_type
    def raise_picker(window, _parameter):
        title = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(window, title, len(title))
        if title.value == data.lpstrTitle and user32.IsWindowVisible(window):
            if user32.SetWindowPos(window, w.HWND(-1), 0, 0, 0, 0, 0x1 | 0x2 | 0x40):
                user32.SetForegroundWindow(window)
                closed.set()
                return False
        return True
    def focus_when_visible():
        deadline = time.monotonic() + 10
        while not closed.wait(0.05) and time.monotonic() < deadline:
            user32.EnumThreadWindows(gui_thread, raise_picker, 0)
    data.Flags = 0x80000 | 0x200 | 0x1000 | 0x800 | 0x8 | 0x2000000
    dialog = ctypes.WinDLL('comdlg32', use_last_error=True)
    dialog.GetOpenFileNameW.argtypes = [ctypes.POINTER(OpenFileName)]
    dialog.GetOpenFileNameW.restype = w.BOOL
    threading.Thread(target=focus_when_visible, daemon=True, name='lingopdf-picker-focus').start()
    try:
        selected = dialog.GetOpenFileNameW(ctypes.byref(data))
    finally:
        closed.set()
    if not selected:
        error = dialog.CommDlgExtendedError()
        if error:
            raise OSError(f'Windows file dialog error: {error}')
        return []
    values = ''.join(buffer).rstrip('\0').split('\0')
    return values if len(values) == 1 else [str(Path(values[0]) / name) for name in values[1:]]


def picker():
    if sys.platform == 'win32':
        return windows_picker()
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    paths = filedialog.askopenfilenames(parent=root, title='LingoPDF - Select source documents',
                                       filetypes=[('Documents','*.pdf *.docx *.pptx *.doc *.ppt')])
    root.destroy()
    return list(paths)


if __name__ == '__main__':
    try:
        print(json.dumps(picker(), ensure_ascii=True))
    except Exception as exc:
        print(json.dumps({'error':str(exc)}))
        sys.exit(1)
