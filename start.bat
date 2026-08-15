@echo off
title LingoPDF - Batch PDF Translator
cd /d "%~dp0"

echo.
echo   ========================================
echo            LingoPDF Launcher
echo       Batch PDF Translation Tool
echo   ========================================
echo.

REM -- Kill process on port 8377 if any --
echo   [..] Checking port 8377...
netstat -ano 2>nul | findstr ":8377" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo   [..] Stopping previous instance...
    powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8377 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }" >nul 2>&1
    timeout /t 2 /nobreak >nul 2>&1
)

REM -- Find Python 3.11+ --
set "PYBIN="

REM Try py launcher first (usually has latest Python)
py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set "PYBIN=py -3.11"
    echo   [OK] Python found via py launcher
    goto :check_venv
)

py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set "PYBIN=py -3.12"
    echo   [OK] Python found via py launcher
    goto :check_venv
)

py -3.13 --version >nul 2>&1
if not errorlevel 1 (
    set "PYBIN=py -3.13"
    echo   [OK] Python found via py launcher
    goto :check_venv
)

REM Try python command - check if version is 3.11+
python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PYBIN=python"
    echo   [OK] Python 3.11+ found
    goto :check_venv
)

REM Python found but too old
python --version >nul 2>&1
if not errorlevel 1 (
    echo   [ERROR] Python version is too old!
    echo   LingoPDF requires Python 3.11 or later.
    echo   Your Python version:
    python --version
    echo.
    echo   Please install Python 3.11+ from https://python.org
    echo   Then run start.bat again.
    echo.
    pause
    exit /b 1
)

echo   [ERROR] Python not found!
echo   Please install Python 3.11+ from https://python.org
echo.
pause
exit /b 1

:check_venv

REM -- Create venv if not exists --
if not exist ".venv\Scripts\python.exe" (
    echo   [..] Creating virtual environment (first run only)...
    %PYBIN% -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        echo   [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo   [OK] Virtual environment created
) else (
    echo   [OK] Virtual environment ready
)

REM -- Check and install deps --
echo   [..] Checking dependencies...
".venv\Scripts\python.exe" -c "import fastapi, uvicorn, openai" >nul 2>&1
if errorlevel 1 (
    echo   [..] Upgrading pip...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org >nul 2>&1
    echo   [..] Installing dependencies (first run, may take a few minutes)...
    ".venv\Scripts\python.exe" -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
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

".venv\Scripts\python.exe" run.py