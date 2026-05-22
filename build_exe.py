#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build script to compile the Python helper into a single standalone executable.
Uses PyInstaller to generate a single-file executable.
"""

import sys
import subprocess
from pathlib import Path


def main():
    # Force output encoding to UTF-8 on Windows to avoid GBK print crashes
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 60)
    print("  Codex Login Bypass Tool - Build Script")
    print("=" * 60)
    
    # Verify pyinstaller is installed
    try:
        import PyInstaller
        print(f"[Info] Found PyInstaller version {PyInstaller.__version__}")
    except ImportError:
        print("[Error] PyInstaller is not installed.")
        print("Please run: pip install pyinstaller")
        sys.exit(1)
        
    script_path = Path(__file__).parent / "codex_auth_helper.py"
    if not script_path.exists():
        print(f"[Error] Source script not found at: {script_path}")
        sys.exit(1)
        
    print(f"[Build] Source: {script_path.name}")
    print("[Build] Running PyInstaller compilation...")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name=codex-auth-helper",
        "--clean",
        str(script_path)
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("  [OK] Build completed successfully!")
            dist_dir = Path(__file__).parent / 'dist'
            print(f"  Executable output directory: {dist_dir}")
            print(f"  Executable file: codex-auth-helper.exe")
            print("=" * 60)
            
            # 1. Create a simple README.txt instructions file for the release package
            readme_txt_path = dist_dir / 'README.txt'
            readme_content = """OpenAI Codex Login Bypass Tool (免手机接码登录一键整合包)

一键整合包包含以下文件：
1. 双击运行.bat (Windows 一键启动脚本)
2. codex-auth-helper.exe (本地配置辅助工具)
3. codex_session_extractor.js (浏览器提取 Token 的 JS 脚本)

使用步骤：
1. 打开浏览器登录 https://chatgpt.com (确保能正常聊天)。
2. 按下 F12 打开开发者工具，切换到 Console (控制台)。
3. 打开 codex_session_extractor.js 文件，复制里面的全部代码，粘贴到控制台回车运行。
4. 运行成功后，配置 JSON 字符串会自动复制到您的剪贴板中。
5. 双击运行双击运行.bat 启动工具，程序会自动识别并应用剪贴板中的配置，并验证登录状态，之后按提示启动 Codex 桌面应用即可。

提示：
- 本工具为开源程序，可在 GitHub 项目地址查看源码：https://github.com/chengchengking/codex-
- Web Session Token 的有效期一般为 10 天左右。过期后如提示未登录，请再次在浏览器重复上述步骤更新配置即可。
"""
            try:
                with open(readme_txt_path, 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                print(f"[Pack] Generated instruction file: {readme_txt_path.name}")
            except Exception as e:
                print(f"[Warning] Failed to generate README.txt: {e}")
                
            # 1.1 Create a simple 双击运行.bat for easy execution on Windows
            bat_path = dist_dir / '双击运行.bat'
            bat_content = """@echo off
title OpenAI Codex 免验证登录辅助工具
chcp 65001 > nul

echo ============================================================
echo        OpenAI Codex Login Bypass Companion Tool
echo ============================================================
echo.
echo 请确保您已经执行了以下两步：
echo 1. 打开浏览器登录 https://chatgpt.com/
echo 2. 在控制台 (F12) 运行 codex_session_extractor.js 复制了 Token
echo.
echo 正在启动辅助工具应用配置...
echo ------------------------------------------------------------
echo.

if exist "codex-auth-helper.exe" (
    "codex-auth-helper.exe"
) else (
    echo [错误] 找不到 codex-auth-helper.exe 主程序，请确保文件没有被杀毒软件误杀。
)

echo.
echo ============================================================
echo 运行结束，按任意键退出窗口...
echo ============================================================
pause > nul
"""
            try:
                with open(bat_path, 'w', encoding='utf-8') as f:
                    f.write(bat_content)
                print(f"[Pack] Generated batch file: {bat_path.name}")
            except Exception as e:
                print(f"[Warning] Failed to generate 双击运行.bat: {e}")
                
            # 2. Package files into a ZIP archive
            import zipfile
            zip_path = dist_dir / 'codex-bypass-login-v1.0.0.zip'
            print(f"[Pack] Creating ZIP archive at: {zip_path}...")
            
            files_to_zip = [
                (dist_dir / 'codex-auth-helper.exe', 'codex-auth-helper.exe'),
                (Path(__file__).parent / 'codex_session_extractor.js', 'codex_session_extractor.js'),
                (readme_txt_path, 'README.txt'),
                (bat_path, '双击运行.bat')
            ]
            
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file_path, arcname in files_to_zip:
                        if file_path.exists():
                            zip_file.write(file_path, arcname)
                            print(f"  + Added to ZIP: {arcname}")
                        else:
                            print(f"[Warning] File not found: {file_path}")
                print(f"[OK] One-click integration package successfully created at: {zip_path.name}")
            except Exception as e:
                print(f"[Error] Failed to create ZIP archive: {e}")
            print("=" * 60)
        else:
            print(f"[Error] PyInstaller exited with code: {result.returncode}")
    except Exception as e:
        print(f"[Error] PyInstaller execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
