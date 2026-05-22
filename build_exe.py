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
            print(f"  Executable output directory: {Path(__file__).parent / 'dist'}")
            print(f"  Executable file: codex-auth-helper.exe")
            print("=" * 60)
        else:
            print(f"[Error] PyInstaller exited with code: {result.returncode}")
    except Exception as e:
        print(f"[Error] PyInstaller execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
