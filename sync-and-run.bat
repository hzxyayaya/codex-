@echo off
chcp 65001 > nul
title Codex Cloudflare Sync and Launch Tool

echo ============================================================
echo      Codex Cloudflare Sync and Launch Tool
echo ============================================================
echo 正在同步您的最新 Codex 凭证...

:: 1. Run the PowerShell sync script
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync-codex.ps1"

:: Check powershell exit code
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [错误] 凭证同步失败，未启动 Codex。
    pause
    exit /b %ERRORLEVEL%
)

:: 2. Locate and launch Codex Desktop
set "CODEX_PATH=%LOCALAPPDATA%\OpenAI\Codex\bin\codex.exe"

if exist "%CODEX_PATH%" (
    echo 发现 Codex 客户端：%CODEX_PATH%
    echo 正在拉起 Codex Desktop 客户端...
    start "" "%CODEX_PATH%" app
    echo [成功] Codex 进程已成功创建。祝您使用愉快！
    timeout /t 3 > nul
) else (
    echo.
    echo [提示] 未在默认路径找到 Codex 客户端程序 (%CODEX_PATH%)。
    echo 凭证已成功更新！您可以手动启动您的 Codex 客户端或 CLI。
    pause
)
