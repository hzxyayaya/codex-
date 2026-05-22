#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenAI Codex Login Bypass Companion Tool
- Automatically reads the formatted JSON from clipboard (requires pyperclip) or manual input.
- Validates the token structure and expiration.
- Backs up existing ~/.codex/auth.json configurations.
- Writes the bypass session token.
- Verifies authentication status using Codex CLI.
- Automatically launches Codex Desktop if requested.
"""

import os
import sys
import json
import base64
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Try importing pyperclip for automatic clipboard extraction
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False


def print_banner():
    banner = """
============================================================
       OpenAI Codex Login Bypass Companion Tool
============================================================
    Bypassing phone/SMS verification using web session token
============================================================
"""
    print(banner)


def check_jwt_expiry(token_str):
    """Parses JWT payload and checks if the token is expired."""
    try:
        parts = token_str.split('.')
        if len(parts) != 3:
            return False, "Invalid JWT format"
        
        # Add padding to base64 string
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
            
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        exp = payload.get('exp')
        if not exp:
            return True, "No exp claim found in JWT, proceeding anyway."
            
        exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        remaining_days = (exp_time - now).days
        remaining_hours = (exp_time - now).seconds // 3600
        
        if now > exp_time:
            return False, f"Token expired on {exp_time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        else:
            return True, f"Token is valid for another {remaining_days} days and {remaining_hours} hours."
    except Exception as e:
        return True, f"Could not determine token expiry ({e}), proceeding anyway."


def locate_codex_bin():
    """Attempts to find the codex binary path on Windows."""
    paths = [
        Path.home() / "AppData" / "Local" / "OpenAI" / "Codex" / "bin" / "codex.exe",
        Path("C:/Users") / os.getlogin() / "AppData" / "Local" / "OpenAI" / "Codex" / "bin" / "codex.exe",
    ]
    for p in paths:
        if p.exists():
            return p
    return None


def run_login_bypass(auth_data):
    """Backs up old configuration, writes the new one, and runs validation."""
    codex_dir = Path.home() / ".codex"
    codex_dir.mkdir(exist_ok=True)
    auth_file = codex_dir / "auth.json"
    
    # 1. Backup existing auth.json
    if auth_file.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = codex_dir / f"auth.json.bak_{timestamp}"
        try:
            auth_file.rename(backup_file)
            print(f"[Backup] Successfully backed up old configuration to: {backup_file.name}")
        except Exception as e:
            print(f"[Warning] Failed to back up existing auth.json: {e}")
            
    # 2. Write new auth.json
    try:
        with open(auth_file, "w", encoding="utf-8") as f:
            json.dump(auth_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] New config successfully written to: {auth_file}")
    except Exception as e:
        print(f"[Error] Failed to write config file: {e}")
        return False

    # 3. Verify status with codex.exe
    codex_path = locate_codex_bin()
    if not codex_path:
        print("[Info] Codex binary not found in standard user paths. Skipping CLI status verification.")
        print("[Info] If you installed Codex in a custom location, please run 'codex login status' manually.")
        return True
        
    print(f"[Verify] Found Codex executable: {codex_path}")
    print("[Verify] Checking authentication status...")
    
    try:
        result = subprocess.run(
            [str(codex_path), "login", "status"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.returncode == 0:
            print(f"[Success] Codex CLI Output: {result.stdout.strip()}")
            return True
        else:
            print(f"[Warning] Codex CLI login check failed (Code {result.returncode})")
            print(f"Error output: {result.stderr.strip() or result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"[Warning] Failed to run codex.exe status check: {e}")
        return True


def prompt_launch_codex():
    """Prompts the user to launch the Codex desktop application."""
    codex_path = locate_codex_bin()
    if not codex_path:
        return
        
    choice = input("\nWould you like to launch Codex Desktop now? (y/n): ").strip().lower()
    if choice in ['y', 'yes', '']:
        print("[Launch] Starting Codex Desktop...")
        try:
            if sys.platform == "win32":
                subprocess.Popen([str(codex_path), "app"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([str(codex_path), "app"])
            print("[Launch] Codex Desktop process spawned. Happy coding!")
        except Exception as e:
            print(f"[Error] Failed to start Codex: {e}")


def main():
    # Force output encoding to UTF-8 on Windows
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')
        
    print_banner()
    
    print("Please select authentication mode:")
    print("1) ChatGPT Web Session Mode (Bypass Phone Verification)")
    print("2) OpenAI API Key Mode (Direct Platform Key)")
    print("-" * 60)
    choice = input("Enter choice (1 or 2, default is 1): ").strip()
    
    auth_data = None
    
    if choice == '2':
        print("\n--- OpenAI API Key Mode ---")
        api_key = input("Enter your OpenAI API Key (starts with sk-): ").strip()
        if not api_key:
            print("[Error] API key cannot be empty. Exiting.")
            sys.exit(1)
        if not api_key.startswith("sk-"):
            print("[Warning] API key typically starts with 'sk-'. Please make sure it is correct.")
        
        auth_data = {
            "auth_mode": "apikey",
            "OPENAI_API_KEY": api_key
        }
    else:
        print("\n--- ChatGPT Web Session Mode ---")
        # Method A: Clipboard auto-detection
        if HAS_PYPERCLIP:
            print("[Clipboard] Checking clipboard for configuration JSON...")
            clipboard_content = pyperclip.paste().strip()
            if clipboard_content.startswith("{") and "auth_mode" in clipboard_content and "access_token" in clipboard_content:
                try:
                    temp_data = json.loads(clipboard_content)
                    if temp_data.get("tokens", {}).get("access_token"):
                        print("[Clipboard] Found valid Codex Bypass JSON configuration in clipboard!")
                        confirm = input("Apply clipboard configuration? (Y/n): ").strip().lower()
                        if confirm in ['y', 'yes', '']:
                            auth_data = temp_data
                except Exception:
                    pass
                    
        if not auth_data:
            if HAS_PYPERCLIP:
                print("[Clipboard] Clipboard did not contain valid config JSON.")
            else:
                print("[Clipboard] Python package 'pyperclip' not installed. Auto clipboard detection disabled.")
                
            print("\nPlease paste the JSON payload retrieved from your browser console below.")
            print("Press ENTER on an empty line or Ctrl+D (Ctrl+Z + Enter on Windows) when done:")
            print("-" * 60)
            
            lines = []
            try:
                while True:
                    line = input()
                    if not line.strip() and lines:  # break on empty line after some text has been entered
                        break
                    lines.append(line)
            except (KeyboardInterrupt, EOFError):
                print()
                
            full_input = "\n".join(lines).strip()
            if not full_input:
                print("[Error] No input detected. Exiting.")
                sys.exit(1)
                
            try:
                auth_data = json.loads(full_input)
            except json.JSONDecodeError as e:
                print(f"[Error] Invalid JSON format: {e}")
                sys.exit(1)

        # Validate JSON keys
        tokens = auth_data.get("tokens", {})
        access_token = tokens.get("access_token")
        
        if not access_token:
            print("[Error] Invalid payload: Missing 'tokens.access_token'. Please ensure you copied the entire JSON.")
            sys.exit(1)
            
        # Check JWT Expiration
        ok, message = check_jwt_expiry(access_token)
        print(f"\n[JWT Status] {message}")
        if not ok:
            print("[Error] Expired token. Please log into https://chatgpt.com/ and extract a fresh token.")
            sys.exit(1)
        
    # Run the setup
    success = run_login_bypass(auth_data)
    if success:
        prompt_launch_codex()
    else:
        print("\n[Error] Login configuration failed. Please check your inputs and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
