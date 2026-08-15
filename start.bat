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
netstat -ano 2>nul | findstr ":8377" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo   [!!] Stopping previous instance...
    powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8377 -ErrorAction SilentlyContinue ^| ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }" ^>nul 2^>^&1
    timeout /t 2 /nobreak >nul 2>&1
)

REM -- Check venv --
if not exist ".venv\Scripts\python.exe" (
    echo   [ERROR] .venv not found!
    echo   Please re-download LingoPDF from GitHub.
    pause
    exit /b 1
)

echo   [OK] Environment ready

REM -- Start server --
echo.
echo   [>>] Starting LingoPDF at http://127.0.0.1:8377
echo   [>>] Browser will open in 3 seconds...
echo   [>>] Close this window to stop LingoPDF.
echo.

start "" /b cmd /c "timeout /t 3 ^>nul ^& start http://127.0.0.1:8377"

".venv\Scripts\python.exe" run.py