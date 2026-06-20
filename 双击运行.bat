@echo off
chcp 65001 > nul
title OpenAI Codex 登录同步助手

echo ============================================================
echo        OpenAI Codex 免验证登录助手 (一键双击运行版)
echo ============================================================
echo.
echo 正在启动本地同步脚本...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0codex-auth-helper.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [提示] 运行中发生异常，请检查网络或浏览器状态。
    pause
)
