@echo off
title OpenAI Codex Login Bypass Tool

echo ============================================================
echo     OpenAI Codex Login Bypass Tool (One-Click Launcher)
echo ============================================================
echo.
echo Launching local PowerShell sync engine...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0codex-auth-helper.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Error] Execution failed. Please check browser status or console errors.
    pause
)
