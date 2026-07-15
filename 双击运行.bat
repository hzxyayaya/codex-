@echo off
cd /d "%~dp0"
title OpenAI Codex Login Bypass Tool

echo ============================================================
echo     OpenAI Codex Login Bypass Tool (One-Click Launcher)
echo ============================================================
echo.

if not exist "%~dp0codex-auth-helper.ps1" (
    echo [Error] codex-auth-helper.ps1 not found in this folder.
    echo Please keep the .bat and .ps1 files together.
    pause
    exit /b 1
)

echo Launching local PowerShell sync engine...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0codex-auth-helper.ps1"
set PS_EXIT=%ERRORLEVEL%

if %PS_EXIT% NEQ 0 (
    echo.
    echo [Error] Execution failed ^(exit code %PS_EXIT%^). Check browser or network.
    pause
    exit /b %PS_EXIT%
)

echo.
echo Done. Press any key to close this window...
pause >nul
