@echo off
title LingoPDF - Batch PDF Translator
cd /d "%~dp0"

echo.
echo   ========================================
echo            LingoPDF Launcher
echo       Batch PDF Translation Tool
echo   ========================================
echo.

REM -- Kill any process using port 8377 --
echo   [..] Checking port 8377...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8377" ^| findstr "LISTENING"') do (
    echo   [..] Stopping previous instance PID %%a
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul 2>&1

REM -- Find Python --
set "PYBIN="
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYBIN=python"
    goto :found_py
)
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYBIN=py -3"
    goto :found_py
)
echo   [ERROR] Python not found!
echo   Please install Python 3.11+ from https://python.org
echo.
pause
exit /b 1

:found_py
echo   [OK] Python: %PYBIN%

REM -- Create venv if not exists --
if not exist ".venv\Scripts\python.exe" (
    echo   [..] Creating virtual environment (first run only)...
    "%PYBIN%" -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        echo   [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo   [OK] Virtual environment created
)

set "PYTHON=.venv\Scripts\python.exe"

REM -- Check and install deps --
echo   [..] Checking dependencies...
"%PYTHON%" -c "import fastapi, uvicorn, openai" >nul 2>&1
if errorlevel 1 (
    echo   [..] Installing dependencies (first run, may take a few minutes)...
    "%PYTHON%" -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org -r requirements.txt
    if errorlevel 1 (
        echo   [ERROR] Failed to install dependencies.
        echo   Please check your network and try:
        echo   pip install -r requirements.txt
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
echo   [>>] Close this window to stop.
echo.

start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:8377"

"%PYTHON%" run.py