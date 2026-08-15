@echo off
title LingoPDF - Batch PDF Translator
cd /d "%~dp0"

echo.
echo   ========================================
echo            LingoPDF Launcher
echo       Batch PDF Translation Tool
echo   ========================================
echo.

REM -- Kill any process on port 8377 --
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8377" ^| findstr "LISTENING"') do (
    echo   [!] Stopping previous instance PID %%a
    taskkill /F /PID %%a >nul 2>&1
)
if exist ".linguapdf.pid" del .linguapdf.pid >nul 2>&1

REM -- Check venv --
if not exist ".venv\Scripts\python.exe" (
    echo   [ERROR] .venv not found!
    echo   Please re-download LingoPDF from GitHub.
    pause
    exit /b 1
)

echo   [OK] Environment ready
echo.
echo   [..] Starting LingoPDF at http://127.0.0.1:8377
echo   [..] Browser will open in 3 seconds...
echo   [..] Close the browser tab to stop LingoPDF.
echo.

REM -- Minimize this window (服务在后台运行，关浏览器即关服务) --
if not "%1"=="--no-min" powershell -command "(New-Object -ComObject WScript.Shell).AppActivate((Get-Process -Name cmd -Id $PID).MainWindowHandle); (New-Object -ComObject WScript.Shell).SendKeys('% ')"

REM -- Open browser after 3 seconds --
start /b cmd /c "ping 127.0.0.1 -n 4 >nul 2>&1 & start http://127.0.0.1:8377"

REM -- Run server (foreground, closes window = kills process) --
".venv\Scripts\python.exe" run.py
