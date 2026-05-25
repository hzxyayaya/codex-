@echo off
title OpenAI Codex Login Bypass Companion Tool

echo ============================================================
echo        OpenAI Codex Login Bypass Companion Tool
echo ============================================================
echo.
echo Launching companion tool...
echo ------------------------------------------------------------
echo.

if exist "dist\codex-auth-helper.exe" (
    "dist\codex-auth-helper.exe"
) else if exist "codex-auth-helper.exe" (
    "codex-auth-helper.exe"
) else (
    echo [Error] Could not find codex-auth-helper.exe main program.
    echo Please make sure it is not blocked or deleted by antivirus software.
)

echo.
echo ============================================================
echo Process finished. Press any key to exit...
echo ============================================================
pause > nul
