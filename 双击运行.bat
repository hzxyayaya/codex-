@echo off
title OpenAI Codex 免验证登录辅助工具

echo ============================================================
echo        OpenAI Codex Login Bypass Companion Tool
echo ============================================================
echo.
echo 正在启动辅助工具应用配置...
echo ------------------------------------------------------------
echo.

if exist "dist\codex-auth-helper.exe" (
    "dist\codex-auth-helper.exe"
) else if exist "codex-auth-helper.exe" (
    "codex-auth-helper.exe"
) else (
    echo [错误] 找不到 codex-auth-helper.exe 主程序。
    echo 请确保在当前目录或 dist 文件夹内存在此程序。
)

echo.
echo ============================================================
echo 运行结束，按任意键退出窗口...
echo ============================================================
pause > nul
