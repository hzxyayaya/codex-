@echo off
chcp 65001 > nul
title 生成朋友专用同步工具包

echo ============================================================
echo          生成朋友专用同步工具包 (一键解压使用版)
echo ============================================================
echo.
echo 您的朋友只需要：
echo 1. 在浏览器点击书签进行同步（无需进行任何复杂的网页文件夹绑定操作）。
echo 2. 在电脑上双击解压后的“双击同步并运行.bat”，即可自动同步并启动 Codex。
echo.
echo ------------------------------------------------------------
set /p SECRET_KEY="请输入您想给朋友使用的“专属同步密钥 (Secret Key)”: "
if "%SECRET_KEY%"=="" (
    echo [错误] 密钥不能为空！
    pause
    exit /b 1
)

set WORKER_URL=https://codex-sync-worker.epidemicsituation.workers.dev

echo.
echo 正在为您生成工具包...
echo ------------------------------------------------------------

:: Create temp directory
set "TEMP_DIR=%~dp0temp_build"
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

:: Copy scripts
copy "%~dp0sync-codex.ps1" "%TEMP_DIR%\sync-codex.ps1" > nul
copy "%~dp0sync-and-run.bat" "%TEMP_DIR%\双击同步并运行.bat" > nul

:: Generate sync-config.json
echo {> "%TEMP_DIR%\sync-config.json"
echo   "WorkerUrl": "%WORKER_URL%",>> "%TEMP_DIR%\sync-config.json"
echo   "SecretKey": "%SECRET_KEY%">> "%TEMP_DIR%\sync-config.json"
echo }>> "%TEMP_DIR%\sync-config.json"

:: Use PowerShell to zip the temp folder
set "ZIP_PATH=%~dp0codex-sync-tool-for-friends.zip"
if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"

powershell -NoProfile -Command "Compress-Archive -Path '%TEMP_DIR%\*' -DestinationPath '%ZIP_PATH%' -Force"

:: Clean up
rd /s /q "%TEMP_DIR%"

echo.
echo ============================================================
echo [成功] 已成功生成朋友专用的同步压缩包！
echo 压缩包文件位置：%ZIP_PATH%
echo.
echo 提示：您可以直接把这个 ZIP 压缩包发送给您的朋友。
echo 让他们解压到电脑任意位置，然后双击运行“双击同步并运行.bat”即可！
echo ============================================================
pause
