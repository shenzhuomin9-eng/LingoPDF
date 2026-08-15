@echo off
chcp 65001 >nul 2>&1
title Create LingoPDF Desktop Shortcut

REM ═══════════════════════════════════════════════════════
REM  在桌面创建 LingoPDF 快捷方式 — 双击即可启动翻译工具
REM ═══════════════════════════════════════════════════════

cd /d "%~dp0"

set "SHORTCUT=%USERPROFILE%\Desktop\LingoPDF.lnk"
set "TARGET=%~dp0start.bat"
set "ICON=%~dp0static\favicon.ico"

echo.
echo   Creating desktop shortcut...
echo   -> %SHORTCUT%
echo.

REM 用 PowerShell 创建快捷方式
powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$sc = $ws.CreateShortcut('%SHORTCUT%'); " ^
  "$sc.TargetPath = '%TARGET%'; " ^
  "$sc.WorkingDirectory = '%~dp0'; " ^
  "$sc.Description = 'LingoPDF - Batch PDF Translator'; " ^
  "$sc.IconLocation = '%ICON%'; " ^
  "$sc.Save()"

if exist "%SHORTCUT%" (
    echo   [OK] Shortcut created on Desktop!
    echo   Double-click "LingoPDF" on your Desktop to start.
) else (
    echo   [ERROR] Failed to create shortcut.
)

echo.
pause