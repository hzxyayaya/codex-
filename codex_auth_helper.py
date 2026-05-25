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
import socket
import urllib.request
import urllib.error
import urllib.parse
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Try importing pyperclip for automatic clipboard extraction
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

# Permanent grafted id_token from a Team subscription account to unlock Codex Desktop GUI locally
GRAFT_ID_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImIxZGQzZjhmLTlhYWQtNDdmZS1iMGU3LWVkYjAwOTc3N2Q2YiIsInR5cCI6IkpXVCJ9.eyJhdF9oYXNoIjoiUWhyUE0ybTBPN3ZqZkhxNW52RzZZQSIsImF1ZCI6WyJhcHBfRU1vYW1FRVo3M2YwQ2tYYVhwN2hyYW5uIl0sImF1dGhfcHJvdmlkZXIiOiJnb29nbGUiLCJhdXRoX3RpbWUiOjE3NzM1NjA0NDgsImVtYWlsIjoibGl3ZW5sb25nMDEyM0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZXhwIjoxNzczNTY0MDUwLCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsiY2hhdGdwdF9hY2NvdW50X2lkIjoiZWFhMGQ3NDQtNTM0Yi00OThiLWFhZjItNDBjOWViYjQ2NGY0IiwiY2hhdGdwdF9wbGFuX3R5cGUiOiJ0ZWFtIiwiY2hhdGdwdF9zdWJzY3JpcHRpb25fYWN0aXZlX3N0YXJ0IjoiMjAyNi0wMy0xNVQwNzoyMDo0NyswMDowMCIsImNoYXRncHRfc3Vic2NyaXB0aW9uX2FjdGl2ZV91bnRpbCI6IjIwMjYtMDQtMTVUMDc6MjA6NDcrMDA6MDAiLCJjaGF0Z3B0X3N1YnNjcmlwdGlvbl9sYXN0X2NoZWNrZWQiOiIyMDI2LTAzLTE1VDA3OjQwOjQ4Ljc0MzY1NCswMDowMCIsImNoYXRncHRfdXNlcl9pZCI6InVzZXItQWlzdjh6ZzU1enNld1V2eTNzRkt2bkZKIiwiZ3JvdXBzIjpbXSwib3JnYW5pemF0aW9ucyI6W3siaWQiOiJvcmctSEM4OE9RYjVFN3o3TXRtTGpDY2NMNWVnIiwiaXNfZGVmYXVsdCI6dHJ1ZSwicm9sZSI6Im93bmVyIiwidGl0bGUiOiJQZXJzb25hbCJ9XSwidXNlcl9pZCI6InVzZXItQWlzdjh6ZzU1enNld1V2eTNzRkt2bkZKIn0sImlhdCI6MTc3MzU2MDQ1MCwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJqdGkiOiMzZmRhN2U5Ny1hOGE1LTQ5ZDItYmVmNS1lZThjYWIzOGI3NTgiLCJyYXQiOjE3NzM1NjAzMzksInNpZCI6IjM2OWMzNGQ2LWEyYjctNDM5Ni1iYjljLWRjMGFiNTU0ZThkOSIsInN1YiI6Imdvb2dsZS1vYXV0aDJ8MTE3MjU1ODk4NjQyMzExMTQxNTM4In0.zvjw9yx33ETCME6uP3gB7W7Sv9ZPdzBtAK5zeN3dk3A64F8yQPOcALu1d7W4vXMD587UxHLK1B0yZGX8kR4M0yjCM14-V92u5hxjHI09ZE0W3CeC7yGMWeUh54hzu25LzbiBTsBM3RQcqrOayrI3G3XrY5EMzDT3sS1jwLKvJranmMs1wUGw59gcA7vOH1hbxSp_RzVF9PPKxxRBqralA4mTqZFSZYaovh9bbxEzLO3Gu6wzWmyHHCzT7ol1YJeqqknNAolEg0VC5EviQl8F6RUO1H0KX4Z6rP4kA6YFEHHRIt9obQIUNE0fS33m00ZTn8DMPlpH69b8sfWa1EzXENyM-GRnK8uhqgiEgTCMyIvwT6nmRjlfO1hOAIe-nRqjFxZVDTCix1kUJeazIYk80w0jQMp2DCqUCYRqvb80uW5ahFYksRDp-TNZSToAzXpaaDHMzzDPhK-nr-Y9s7oGMrxA8N9Lh9LdXHNJH16kqMge3cVWiVbS6nNSrT-Mf8EyfuHDDf_KpqD5EsdIVm2azTFqVutORdAEd_eCf-77fmNQo-puxwEVNkgEVRc1IAV1AwzxuBNWy-28XSjehAGeyaC4wb7Dcl_7X1w43JwFoNe4kgoq0ugWbYVwQ_NYUL8KkkW4GEEuqLTjU5CSHalikNz8Z_mBBjGN_M5Fs_zZzW4"


def find_browser():
    """Finds Chrome or Edge executable on Windows, checking registry first."""
    # 1. Try finding Chrome or Edge via Windows Registry
    if sys.platform == "win32":
        import winreg
        for reg_path in [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"
        ]:
            for key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    with winreg.OpenKey(key, reg_path) as k:
                        val, _ = winreg.QueryValueEx(k, "")
                        if val and os.path.exists(val):
                            return val
                except Exception:
                    pass

    # 2. Hardcoded fallback list (including D: and C: drives)
    paths = [
        # Chrome paths
        r"D:\Program Files\Google\Chrome\Application\chrome.exe",
        r"D:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        # Edge paths
        r"D:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"D:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def ws_handshake(sock, host, path):
    key = "dGhlIHNhbXBsZSBub25jZQ=="  # standard dummy key
    handshake = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    )
    sock.sendall(handshake.encode())
    
    response = b""
    while b"\r\n\r\n" not in response:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    
    headers, body = response.split(b"\r\n\r\n", 1)
    status_line = headers.split(b"\r\n")[0]
    if b"101" not in status_line:
        raise Exception("Handshake failed: " + headers.decode(errors='ignore'))
    return body


def ws_send(sock, text):
    data = text.encode('utf-8')
    length = len(data)
    frame = bytearray([0x81])
    
    if length <= 125:
        frame.append(0x80 | length)
    elif length <= 65535:
        frame.append(0x80 | 126)
        frame.extend(length.to_bytes(2, 'big'))
    else:
        frame.append(0x80 | 127)
        frame.extend(length.to_bytes(8, 'big'))
        
    mask = bytearray([0x01, 0x02, 0x03, 0x04])
    frame.extend(mask)
    
    masked_data = bytearray(length)
    for i in range(length):
        masked_data[i] = data[i] ^ mask[i % 4]
    frame.extend(masked_data)
    
    sock.sendall(frame)


def ws_recv(sock, buffered_data=b""):
    data = buffered_data
    
    def read_bytes(n):
        nonlocal data
        while len(data) < n:
            chunk = sock.recv(4096)
            if not chunk:
                raise Exception("Connection closed")
            data += chunk
        res = data[:n]
        data = data[n:]
        return res

    header = read_bytes(2)
    fin_opcode = header[0]
    mask_len = header[1]
    
    masked = bool(mask_len & 0x80)
    length = mask_len & 0x7f
    
    if length == 126:
        length_bytes = read_bytes(2)
        length = int.from_bytes(length_bytes, 'big')
    elif length == 127:
        length_bytes = read_bytes(8)
        length = int.from_bytes(length_bytes, 'big')
        
    if masked:
        mask = read_bytes(4)
        
    payload = read_bytes(length)
    if masked:
        unmasked = bytearray(length)
        for i in range(length):
            unmasked[i] = payload[i] ^ mask[i % 4]
        payload = bytes(unmasked)
        
    return payload.decode('utf-8'), data


def evaluate_js(ws_url, expression):
    parsed = urllib.parse.urlparse(ws_url)
    host = parsed.netloc
    path = parsed.path
    if parsed.query:
        path += "?" + parsed.query
        
    host_parts = host.split(":")
    ip = host_parts[0]
    port = int(host_parts[1]) if len(host_parts) > 1 else 80
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    
    buffered = ws_handshake(sock, host, path)
    
    cmd = {
        "id": 1,
        "method": "Runtime.evaluate",
        "params": {
            "expression": expression,
            "awaitPromise": True,
            "returnByValue": True
        }
    }
    
    ws_send(sock, json.dumps(cmd))
    
    while True:
        msg, buffered = ws_recv(sock, buffered)
        res = json.loads(msg)
        if res.get("id") == 1:
            sock.close()
            return res.get("result", {})


def extract_account_id(token_str):
    try:
        parts = token_str.split('.')
        if len(parts) == 3:
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_bytes.decode('utf-8'))
            auth_info = payload.get("https://api.openai.com/auth", {})
            return auth_info.get("chatgpt_account_id", "")
    except Exception:
        pass
    return ""


def run_auto_retrieve():
    browser_path = find_browser()
    if not browser_path:
        print("\033[93m[自动获取] 提示：未在系统中找到安装的 Chrome 或 Edge 浏览器。\033[0m")
        return None
        
    port = 9333
    user_dir = Path.home() / ".codex" / "browser_session"
    user_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        browser_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_dir}",
        "https://chatgpt.com/",
    ]
    
    print("\n\033[96m[自动获取] 🚀 正在为您启动 Chrome/Edge 独立浏览器窗口...\033[0m")
    print("\033[94m============================================================\033[0m")
    print("\033[92m 【第一步】如果浏览器显示未登录，请在弹出的窗口中登录您的 ChatGPT 账号。\033[0m")
    print("\033[92m 【第二步】登录成功并进入聊天界面后，本工具会自动捕获 Token 并自动关闭浏览器！\033[0m")
    print("\033[94m============================================================\033[0m")
    print("\033[93m 正在连接浏览器并检测登录状态，最长等待 3 分钟... (随时按 Ctrl+C 切换为手动模式)\033[0m")
    
    try:
        # Launch browser VISIBLY (do NOT use CREATE_NO_WINDOW for GUI programs!)
        proc = subprocess.Popen(cmd)
    except Exception as e:
        print(f"\033[91m[自动获取] 启动浏览器失败: {e}\033[0m")
        return None
        
    targets = []
    for _ in range(15):
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
            targets = json.loads(req.read().decode('utf-8'))
            break
        except Exception:
            time.sleep(1)
            
    if not targets:
        print("\033[91m[自动获取] 错误：无法连接到浏览器调试接口。\033[0m")
        try:
            proc.terminate()
        except:
            pass
        return None
        
    js_expr = """
    fetch('/api/auth/session')
      .then(r => r.json())
      .then(data => {
         if (data && data.accessToken) {
           return { success: true, token: data.accessToken };
         } else {
           return { success: false, reason: 'not_logged_in' };
         }
      })
      .catch(err => {
         return { success: false, reason: err.message };
      })
    """
    
    start_time = time.time()
    auth_data = None
    
    try:
        while time.time() - start_time < 180:
            try:
                req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
                targets = json.loads(req.read().decode('utf-8'))
            except Exception:
                print("\n\033[93m[自动获取] 提示：与浏览器连接断开，请确保浏览器窗口未被关闭。\033[0m")
                time.sleep(2)
                continue
                
            chatgpt_target = None
            for t in targets:
                if t.get("type") == "page" and "chatgpt.com" in t.get("url", "").lower():
                    chatgpt_target = t
                    break
                    
            if not chatgpt_target:
                time.sleep(2)
                continue
                
            ws_url = chatgpt_target.get("webSocketDebuggerUrl")
            if not ws_url:
                time.sleep(2)
                continue
                
            try:
                eval_res = evaluate_js(ws_url, js_expr)
                res_val = eval_res.get("result", {}).get("value", {})
                if isinstance(res_val, dict):
                    if res_val.get("success"):
                        token = res_val.get("token")
                        account_id = extract_account_id(token)
                        auth_data = {
                            "auth_mode": "chatgpt",
                            "OPENAI_API_KEY": None,
                            "tokens": {
                                "id_token": token,
                                "access_token": token,
                                "refresh_token": "",
                                "account_id": account_id
                            },
                            "last_refresh": datetime.now(timezone.utc).isoformat()
                        }
                        print("\n\033[92m[自动获取] ✓ 成功捕获到活跃的 ChatGPT 会话！正在自动保存配置...\033[0m")
                        break
                    else:
                        elapsed = int(time.time() - start_time)
                        sys.stdout.write(f"\r\033[93m[自动获取] 正在等待网页登录中... (已等待 {elapsed} 秒 / 最长 180 秒)\033[0m")
                        sys.stdout.flush()
            except Exception:
                pass
                
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\033[93m[自动获取] 用户手动取消了自动获取，正在切换至手动模式...\033[0m")
    finally:
        try:
            proc.terminate()
        except:
            pass
            
    if auth_data:
        return auth_data
    else:
        print("\n\033[91m[自动获取] 自动获取超时或失败。\033[0m")
        return None


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


def optimize_config_toml(plan_type):
    """Automatically optimizes config.toml model configurations based on the user's plan tier."""
    config_path = Path.home() / ".codex" / "config.toml"
    if not config_path.exists():
        return
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        modified = False
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("model ="):
                # Downgrade to lightweight mini models for free accounts to ensure access
                if plan_type == "free":
                    new_lines.append('model = "gpt-5-codex-mini"\n')
                    modified = True
                else:
                    new_lines.append('model = "gpt-5.5"\n')
                    modified = True
            elif stripped.startswith("model_reasoning_effort ="):
                if plan_type == "free":
                    new_lines.append('model_reasoning_effort = "low"\n')
                    modified = True
                else:
                    new_lines.append('model_reasoning_effort = "xhigh"\n')
                    modified = True
            else:
                new_lines.append(line)
                
        if modified:
            # Backup config.toml
            bak_path = config_path.with_name("config.toml.bak")
            shutil.copyfile(config_path, bak_path)
            with open(config_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            print(f"[自适应优化] 检测到您的账户为 {plan_type} 订阅，已自动优化 config.toml 的模型参数！")
    except Exception as e:
        print(f"[自适应警告] 自动优化 config.toml 失败: {e}")


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
        
        # Trigger dynamic model optimization based on plan type
        tokens = auth_data.get("tokens", {})
        access_token = tokens.get("access_token")
        plan_type = "free"
        try:
            parts = access_token.split('.')
            if len(parts) == 3:
                payload_b64 = parts[1]
                padding = 4 - len(payload_b64) % 4
                if padding != 4:
                    payload_b64 += "=" * padding
                payload_bytes = base64.urlsafe_b64decode(payload_b64)
                payload = json.loads(payload_bytes.decode('utf-8'))
                plan_type = payload.get("https://api.openai.com/auth", {}).get("chatgpt_plan_type", "free")
        except Exception:
            pass
        optimize_config_toml(plan_type)
        
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
    
    auth_data = None
    
    # Start auto-retrieve directly without menus
    print("\033[94m正在为您启动一键免手机验证登录获取流程...\033[0m")
    
    try:
        auth_data = run_auto_retrieve()
    except KeyboardInterrupt:
        print("\n\033[93m[提示] 自动获取已取消，正在切换至手动模式...\033[0m")
        auth_data = None
    except Exception as e:
        print(f"\n\033[91m[提示] 自动获取失败 ({e})，正在切换至手动模式...\033[0m")
        auth_data = None
        
    if not auth_data:
        # Fallback to manual clipboard or paste mode
        if HAS_PYPERCLIP:
            print("\n\033[96m[剪贴板] 正在检查剪贴板中是否存在有效的 Token JSON...\033[0m")
            clipboard_content = pyperclip.paste().strip()
            if clipboard_content.startswith("{") and "auth_mode" in clipboard_content and "access_token" in clipboard_content:
                try:
                    temp_data = json.loads(clipboard_content)
                    if temp_data.get("tokens", {}).get("access_token"):
                        print("\n\033[92m[剪贴板] 发现剪贴板中已存在有效的免接码 Token 配置！\033[0m")
                        confirm = input("是否直接应用该剪贴板配置？(Y/n): ").strip().lower()
                        if confirm in ['y', 'yes', '']:
                            auth_data = temp_data
                except Exception:
                    pass
                    
        if not auth_data:
            if HAS_PYPERCLIP:
                print("\033[93m[剪贴板] 剪贴板中未包含有效的配置 JSON，请使用以下手动提取方式：\033[0m")
            else:
                print("\033[93m[剪贴板] 未检测到 pyperclip 模块，请使用以下手动提取方式：\033[0m")
                
            print("\n\033[94m========================= 【手动提取步骤】 =========================\033[0m")
            print("1. 在您的默认浏览器中登录：https://chatgpt.com/")
            print("2. 按 F12 键打开“开发者工具”并切换到 Console（控制台）面板。")
            print("3. 复制 codex_session_extractor.js 脚本中的全部代码粘贴进控制台，并回车运行。")
            print("4. 控制台会自动提示复制成功。回到本窗口，直接在下方粘贴并回车即可！")
            print("\033[94m====================================================================\033[0m")
            print("\n请在下方粘贴浏览器控制台输出的完整 JSON 内容（完成后按一次回车或按 Ctrl+Z + 回车）：")
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
                print("\033[91m[Error] 未检测到任何输入，正在退出程序...\033[0m")
                sys.exit(1)
                
            try:
                auth_data = json.loads(full_input)
            except json.JSONDecodeError as e:
                print(f"\033[91m[Error] JSON 格式解析失败: {e}\033[0m")
                sys.exit(1)

    # Apply Token Grafting automatically!
    if auth_data and "tokens" in auth_data:
        auth_data["tokens"]["id_token"] = GRAFT_ID_TOKEN
        print("\n\033[92m[Token 嫁接] ✓ 已自动为您进行 Token 嫁接配置（将 id_token 替换为 Team 级令牌以解锁客户端 GUI）。\033[0m")

    # Validate JSON keys
    tokens = auth_data.get("tokens", {})
    access_token = tokens.get("access_token")
    
    if not access_token:
        print("\033[91m[Error] 无效的配置数据：缺少 'tokens.access_token'。请确保复制了完整的 JSON。\033[0m")
        sys.exit(1)
        
    # Check JWT Expiration
    ok, message = check_jwt_expiry(access_token)
    print(f"\n[JWT Status] {message}")
    if not ok:
        print("\033[91m[Error] Token 已过期。请登录 https://chatgpt.com/ 提取最新的 Token。\033[0m")
        sys.exit(1)
        
    # Run the setup
    success = run_login_bypass(auth_data)
    if success:
        prompt_launch_codex()
    else:
        print("\n\033[91m[Error] 配置写入失败。请检查权限与输入后重试。\033[0m")
        sys.exit(1)



if __name__ == "__main__":
    main()
