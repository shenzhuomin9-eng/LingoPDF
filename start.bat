@echo off
title LingoPDF - Batch PDF Translator

REM ============================================
REM  LingoPDF Launcher - Double-click to run
REM ============================================

cd /d "%~dp0"

echo.
echo   ========================================
echo            LingoPDF Launcher
echo       Batch PDF Translation Tool
echo   ========================================
echo.

REM -- Find Python --
set "PYTHON="

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    echo   [OK] Found project venv
    goto :found_python
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=python"
    echo   [OK] Found system Python
    goto :found_python
)

py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=py -3"
    echo   [OK] Found Python via py launcher
    goto :found_python
)

echo   [ERROR] Python not found!
echo   Please install Python 3.11+ from https://python.org
echo.
pause
exit /b 1

:found_python

REM -- Check core deps --
echo   [..] Checking dependencies...
"%PYTHON%" -c "import fastapi, uvicorn, openai" >nul 2>&1
if errorlevel 1 (
    echo   [..] Installing dependencies, please wait...
    "%PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo   [ERROR] Failed to install dependencies.
        echo   Try manually: pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo   [OK] Dependencies installed
) else (
    echo   [OK] Dependencies ready
)

REM -- Start server --
echo.
echo   [>>] Starting LingoPDF at http://127.0.0.1:8377
echo   [>>] Browser will open in 3 seconds...
echo   [>>] Press Ctrl+C to stop.
echo.

start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:8377"

"%PYTHON%" run.py
pause