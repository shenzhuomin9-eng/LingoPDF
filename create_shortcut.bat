@echo off
title Create LingoPDF Desktop Shortcut

REM ============================================
REM  Create LingoPDF desktop shortcut
REM ============================================

cd /d "%~dp0"

echo.
echo   Creating desktop shortcut...

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_make_shortcut.ps1"

if exist "%USERPROFILE%\Desktop\LingoPDF.lnk" (
    echo   [OK] Shortcut created on Desktop!
    echo   Double-click "LingoPDF" on your Desktop to start.
) else (
    echo   [ERROR] Failed to create shortcut.
)

echo.
timeout /t 3 /nobreak >nul 2>&1