#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenAI Codex Real Client OAuth Auto-Login & SMS Bypass Tool (Zero-Port Conflict Version)
- Leverages the already running codex.exe daemon on port 1455 to capture redirect.
- Launches Google Chrome (调试端口 9333) with the official Codex Client OAuth authorization URL.
- Backed by WebSocket DevTools Protocol (CDP) to monitor and automate the login flow.
- NEW: Automatically clicks the Microsoft account (li18656872126@outlook.com / Smith) on the choose-an-account screen!
- If OpenAI displays the phone verification (SMS Wall) screen, it automatically queries hero-sms.com for the cheapest countries, rents a number, injects it, clicks send, waits for OTP, and submits it.
- Once successfully authenticated, codex.exe on port 1455 captures the code and writes to ~/.codex/auth.json.
- This script monitors ~/.codex/auth.json, automatically applies the Team Grafting bypass upon modification, and launches Codex Desktop!
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
import secrets
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# ==================== 用户配置 ====================
# 你的 hero-sms.com API Key
HERO_SMS_API_KEY = "1bedd8fd119Afc05ed8f44ce236d2ef6"

# OpenAI/ChatGPT 的接码服务代码，标准为 "ot"
SERVICE_CODE = "ot"

# 每一个接码号码等待短信的最长超时时间（秒）
SMS_TIMEOUT = 120

# 永久嫁接 id_token (Team Bypass)
GRAFT_ID_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImIxZGQzZjhmLTlhYWQtNDdmZS1iMGU3LWVkYjAwOTc3N2Q2YiIsInR5cCI6IkpXVCJ9.eyJhdF9oYXNoIjoiUWhyUE0ybTBPN3ZqZkhxNW52RzZZQSIsImF1ZCI6WyJhcHBfRU1vYW1FRVo3M2YwQ2tYYVhwN2hyYW5uIl0sImF1dGhfcHJvdmlkZXIiOiJnb29nbGUiLCJhdXRoX3RpbWUiOjE3NzM1NjA0NDgsImVtYWlsIjoibGl3ZW5sb25nMDEyM0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZXhwIjoxNzczNTY0MDUwLCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsiY2hhdGdwdF9hY2NvdW50X2lkIjoiZWFhMGQ3NDQtNTM0Yi00OThiLWFhZjItNDBjOWViYjQ2NGY0IiwiY2hhdGdwdF9wbGFuX3R5cGUiOiJ0ZWFtIiwiY2hhdGdwdF9zdWJzY3JpcHRpb25fYWN0aXZlX3N0YXJ0IjoiMjAyNi0wMy0xNVQwNzoyMDo0NyswMDowMCIsImNoYXRncHRfc3Vic2NyaXB0aW9uX2FjdGl2ZV91bnRpbCI6IjIwMjYtMDQtMTVUMDc6MjA6NDcrMDA6MDAiLCJjaGF0Z3B0X3N1YnNjcmlwdGlvbl9sYXN0X2NoZWNrZWQiOiIyMDI2LTAzLTE1VDA3OjQwOjQ4Ljc0MzY1NCswMDowMCIsImNoYXRncHRfdXNlcl9pZCI6InVzZXItQWlzdjh6ZzU1enNld1V2eTNzRkt2bkZKIiwiZ3JvdXBzIjpbXSwib3JnYW5pemF0aW9ucyI6W3siaWQiOiJvcmctSEM4OE9RYjVFN3o3TXRtTGpDY2NMNWVnIiwiaXNfZGVmYXVsdCI6dHJ1ZSwicm9sZSI6Im93bmVyIiwidGl0bGUiOiJQZXJzb25hbCJ9XSwidXNlcl9pZCI6InVzZXItQWlzdjh6ZzU1enNld1V2eTNzRkt2bkZKIn0sImlhdCI6MTc3MzU2MDQ1MCwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJqdGkiOiIzZmRhN2U5Ny1hOGE1LTQ5ZDItYmVmNS1lZThjYWIzOGI3NTgiLCJyYXQiOjE3NzM1NjAzMzksInNpZCI6IjM2OWMzNGQ2LWEyYjctNDM5Ni1iYjljLWRjMGFiNTU0ZThkOSIsInN1YiI6Imdvb2dsZS1vYXV0aDJ8MTE3MjU1ODk4NjQyMzExMTQxNTM4In0.zvjw9yx33ETCME6uP3gB7W7Sv9ZPdzBtAK5zeN3dk3A64F8yQPOcALu1d7W4vXMD587UxHLK1B0yZGX8kR4M0yjCM14-V92u5hxjHI09ZE0W3CeC7yGMWeUh54hzu25LzbiBTsBM3RQcqrOayrI3G3XrY5EMzDT3sS1jwLKvJranmMs1wUGw59gcA7vOH1hbxSp_RzVF9PPKxxRBqralA4mTqZFSZYaovh9bbxEzLO3Gu6wzWmyHHCzT7ol1YJeqqknNAolEg0VC5EviQl8F6RUO1H0KX4Z6rP4kA6YFEHHRIt9obQIUNE0fS33m00ZTn8DMPlpH69b8sfWa1EzXENyM-GRnK8uhqgiEgTCMyIvwT6nmRjlfO1hOAIe-nRqjFxZVDTCix1kUJeazIYk80w0jQMp2DCqUCYRqvb80uW5ahFYksRDp-TNZSToAzXpaaDHMzzDPhK-nr-Y9s7oGMrxA8N9Lh9LdXHNJH16kqMge3cVWiVbS6nNSrT-Mf8EyfuHDDf_KpqD5EsdIVm2azTFqVutORdAEd_eCf-77fmNQo-puxwEVNkgEVRc1IAV1AwzxuBNWy-28XSjehAGeyaC4wb7Dcl_7X1w43JwFoNe4kgoq0ugWbYVwQ_NYUL8KkkW4GEEuqLTjU5CSHalikNz8Z_mBBjGN_M5Fs_zZzW4"
# ==================================================

HERO_SMS_BASE_URL = "https://api.hero-sms.com/stubs/handler_api.php"

# Color Codes
C_GREEN = "\033[92m"
C_RED = "\033[91m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_END = "\033[0m"
C_BOLD = "\033[1m"

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def generate_pkce_pair():
    verifier = base64url_encode(secrets.token_bytes(64))
    sha256 = hashlib.sha256(verifier.encode('ascii')).digest()
    challenge = base64url_encode(sha256)
    return verifier, challenge

def find_browser():
    if sys.platform == "win32":
        import winreg
        for reg_path in [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
        ]:
            for key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    with winreg.OpenKey(key, reg_path) as k:
                        val, _ = winreg.QueryValueEx(k, "")
                        if val and os.path.exists(val):
                            return val
                except Exception:
                    pass
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"D:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

# ==================== WebSocket CDP Implementation ====================
def ws_handshake(sock, host, path):
    key = "dGhlIHNhbXBsZSBub25jZQ=="
    handshake = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n\r\n"
    )
    sock.sendall(handshake.encode())
    
    response = b""
    while b"\r\n\r\n" not in response:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    
    headers, _ = response.split(b"\r\n\r\n", 1)
    status_line = headers.split(b"\r\n")[0]
    if b"101" not in status_line:
        raise Exception("Handshake failed: " + headers.decode(errors='ignore'))

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

def ws_recv(sock):
    header = sock.recv(2)
    if not header or len(header) < 2:
        raise Exception("Connection closed")
    mask_len = header[1]
    masked = bool(mask_len & 0x80)
    length = mask_len & 0x7f
    if length == 126:
        length_bytes = sock.recv(2)
        length = int.from_bytes(length_bytes, 'big')
    elif length == 127:
        length_bytes = sock.recv(8)
        length = int.from_bytes(length_bytes, 'big')
        
    if masked:
        mask = sock.recv(4)
        
    payload = b""
    while len(payload) < length:
        chunk = sock.recv(length - len(payload))
        if not chunk:
            raise Exception("Connection closed")
        payload += chunk
        
    if masked:
        unmasked = bytearray(length)
        for i in range(length):
            unmasked[i] = payload[i] ^ mask[i % 4]
        payload = bytes(unmasked)
    return payload.decode('utf-8')

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
    ws_handshake(sock, host, path)
    
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
    
    response_data = None
    while True:
        msg = ws_recv(sock)
        res = json.loads(msg)
        if res.get("id") == 1:
            response_data = res.get("result", {})
            break
    sock.close()
    return response_data

# ==================== Hero-SMS API Helpers ====================
def make_hero_request(params):
    params["api_key"] = HERO_SMS_API_KEY
    try:
        url = HERO_SMS_BASE_URL + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        print(f"[WARN] Hero-SMS API 请求异常: {e}")
        return None

def get_cheapest_countries():
    print(f"{C_CYAN}[SEARCH] 正在向 Hero-SMS 查询价格最低且有货的国家...{C_END}")
    try:
        url = f"{HERO_SMS_BASE_URL}?api_key={HERO_SMS_API_KEY}&action=getPrices&service={SERVICE_CODE}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.loads(res.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR] 价格列表拉取失败: {e}")
        return []
        
    cheapest_list = []
    for country_id, services in data.items():
        if SERVICE_CODE in services:
            cost = float(services[SERVICE_CODE].get("cost", 999))
            count = int(services[SERVICE_CODE].get("count", 0))
            if count > 0:
                cheapest_list.append({
                    "country_id": country_id,
                    "price": cost,
                    "stock": count
                })
    cheapest_list.sort(key=lambda x: x["price"])
    return cheapest_list

def rent_number(country_id):
    res = make_hero_request({
        "action": "getNumber",
        "service": SERVICE_CODE,
        "country": country_id
    })
    if not res:
        return None
    if "ACCESS_NUMBER" in res:
        parts = res.split(":")
        return {"id": parts[1], "number": parts[2]}
    return res

def check_sms_status(activation_id):
    return make_hero_request({"action": "getStatus", "id": activation_id})

def set_activation_status(activation_id, status):
    return make_hero_request({"action": "setStatus", "status": status, "id": activation_id})

# ==================== 自动化核心逻辑 ====================
def extract_account_id(token_str):
    try:
        parts = token_str.split('.')
        if len(parts) == 3:
            payload_bytes = base64.urlsafe_b64decode(parts[1] + "==")
            payload = json.loads(payload_bytes.decode('utf-8'))
            return payload.get("https://api.openai.com/auth", {}).get("chatgpt_account_id", "")
    except Exception:
        pass
    return ""

def get_future_graft_token():
    try:
        parts = GRAFT_ID_TOKEN.split('.')
        payload_bytes = base64.urlsafe_b64decode(parts[1] + "==")
        payload = json.loads(payload_bytes.decode('utf-8'))
        payload['exp'] = int(time.time()) + 365 * 24 * 3600 * 20
        if 'https://api.openai.com/auth' in payload:
            payload['https://api.openai.com/auth']['chatgpt_subscription_active_until'] = '2046-01-01T00:00:00+00:00'
        new_payload = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8').rstrip('=')
        return f"{parts[0]}.{new_payload}.{parts[2]}"
    except Exception:
        return GRAFT_ID_TOKEN

def locate_codex_bin():
    paths = [
        Path.home() / "AppData" / "Local" / "OpenAI" / "Codex" / "bin" / "codex.exe",
        Path("C:/Users") / os.getlogin() / "AppData" / "Local" / "OpenAI" / "Codex" / "bin" / "codex.exe"
    ]
    for p in paths:
        if p.exists():
            return p
    return None

def run_main_flow():
    print("=" * 70)
    print(f" {C_BOLD}{C_GREEN}        OpenAI Codex 官方桌面客户端全自动一键授权 & 接码系统 (免端口冲突版){C_END}")
    print("=" * 70)
    
    browser_path = find_browser()
    if not browser_path:
        print(f"{C_RED}[ERROR] 系统未检测到 Chrome 浏览器，无法完成自动化动作！{C_END}")
        sys.exit(1)

    # 1. 监控 ~/.codex/auth.json 以获取 codex.exe 完成登录的时间
    codex_dir = Path.home() / ".codex"
    auth_file = codex_dir / "auth.json"
    
    initial_mtime = auth_file.stat().st_mtime if auth_file.exists() else 0
    print(f"[OK] 正在静默监控 {auth_file} 的写入状态...")

    # 2. 构建官方授权跳转 URL
    port_oauth = 1455
    redirect_uri = f"http://localhost:{port_oauth}/auth/callback"
    verifier, challenge = generate_pkce_pair()
    state = secrets.token_hex(16)

    params = {
        "response_type": "code",
        "client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
        "redirect_uri": redirect_uri,
        "scope": "openid profile email offline_access",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
        "id_token_add_organizations": "true",
        "codex_cli_simplified_flow": "true",
        "originator": "pi"
    }
    
    auth_url = "https://auth.openai.com/oauth/authorize?" + urllib.parse.urlencode(params)
    port_cdp = 9333
    user_dir = Path.home() / ".codex" / "browser_session"
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # 优先读取桌面 Chrome 快捷方式的真实路径
    lnk_path = r"C:\Users\chengcheng\Desktop\Google Chrome.lnk"
    resolved_path = None
    if os.path.exists(lnk_path):
        try:
            cmd_lnk = ["powershell", "-NoProfile", "-Command", f"(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk_path}').TargetPath"]
            res_lnk = subprocess.run(cmd_lnk, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            resolved_path = res_lnk.stdout.strip()
        except Exception:
            pass
            
    if resolved_path and os.path.exists(resolved_path):
        real_browser_path = resolved_path
    else:
        real_browser_path = browser_path
        
    print(f"[Browser] 正在启动 Chrome 浏览器并导航至 Codex 客户端登录页面...")
    cmd = [
        real_browser_path,
        f"--remote-debugging-port={port_cdp}",
        f"--user-data-dir={user_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        auth_url
    ]
    proc = subprocess.Popen(cmd)
    
    # 等待浏览器 CDP 端口开放并握手
    ws_url = None
    for _ in range(30):
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:{port_cdp}/json", timeout=2)
            targets = json.loads(req.read().decode('utf-8'))
            for t in targets:
                t_url = t.get("url", "").lower()
                if t.get("type") == "page" and ("openai.com" in t_url or "localhost" in t_url):
                    ws_url = t.get("webSocketDebuggerUrl")
                    break
            if ws_url:
                break
        except Exception:
            pass
        time.sleep(0.5)
        
    if not ws_url:
        print(f"{C_RED}[ERROR] 无法建立与 Chrome 浏览器的调试通道连接。{C_END}")
        sys.exit(1)
        
    print(f"{C_GREEN}[OK] 与 Chrome 浏览器的调试通道握手成功！{C_END}")
    
    sms_state = "idle"  # idle -> testing -> sms_waiting
    active_activation_id = None
    cheapest_countries = []
    current_country_index = 0
    start_wait_time = 0
    
    # 3. 实时的检测与拦截循环
    while True:
        time.sleep(1.5)
        
        # A. 检查 auth.json 是否已被 codex.exe 修改
        if auth_file.exists():
            current_mtime = auth_file.stat().st_mtime
            if current_mtime > initial_mtime:
                print(f"\n{C_GREEN}[SUCCESS] 检测到 codex.exe 已成功写入令牌包！正在对其进行 Team Grafting 提权...{C_END}")
                time.sleep(0.5)
                try:
                    with open(auth_file, "r", encoding="utf-8") as f:
                        auth_data = json.load(f)
                    
                    auth_data["tokens"]["id_token"] = get_future_graft_token()
                    auth_data["last_refresh"] = int(time.time())
                    
                    with open(auth_file, "w", encoding="utf-8") as f:
                        json.dump(auth_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"{C_GREEN}[OK] 成功部署最新 Grafted Token 至 ~/.codex/auth.json！{C_END}")
                except Exception as e:
                    print(f"{C_RED}[ERROR] 提权失败: {e}{C_END}")
                    
                codex_path = locate_codex_bin()
                if codex_path:
                    print("[Spawn] 正在拉起 OpenAI Codex 桌面客户端程序...")
                    subprocess.Popen([str(codex_path), "app"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                break

        # B. 实时检测当前活动页面的 DOM
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:{port_cdp}/json", timeout=2)
            targets = json.loads(req.read().decode('utf-8'))
        except Exception:
            print(f"\n{C_RED}[Browser] 调试器端口断开，浏览器已关闭，测试终止。{C_END}")
            break
            
        chat_target = None
        for t in targets:
            t_url = t.get("url", "").lower()
            if t.get("type") == "page" and ("openai.com" in t_url or "localhost" in t_url):
                chat_target = t
                break
                
        if not chat_target:
            continue
            
        ws_url = chat_target.get("webSocketDebuggerUrl")
        
        # NEW: 增加自动点击 Microsoft 账号登录的 JS 逻辑，实现真正的 100% 免手控！
        js_auto_click_account = """
        (function() {
            // 检测是否处于 auth.openai.com/choose-an-account 或类似的选择账户界面
            if (location.href.includes("choose-an-account") || document.body.textContent.includes("选择一个帐户以继续")) {
                const buttons = Array.from(document.querySelectorAll('button, div, [role="button"], a'));
                const target = buttons.find(el => el.textContent.includes("li18656872126@outlook.com") || el.textContent.includes("Smith"));
                if (target) {
                    target.click();
                    return "clicked_microsoft_account";
                }
            }
            return "no_account_action";
        })()
        """
        try:
            click_res = evaluate_js(ws_url, js_auto_click_account).get("result", {}).get("value", "")
            if click_res == "clicked_microsoft_account":
                print(f"{C_GREEN}[OK] 已自动在网页中点击选择 Microsoft 账户 (li18656872126@outlook.com)！{C_END}")
        except Exception:
            pass
            
        js_detect_phone = """
        (function() {
            const telInput = document.querySelector('input[type="tel"], input[autocomplete*="tel"], input[name*="phone"], input[aria-label*="phone"]');
            const submitBtn = document.querySelector('button[type="submit"], button[aria-label*="send"], button[class*="submit"], button[class*="send"]');
            let btn = submitBtn;
            if (!btn) {
                const buttons = Array.from(document.querySelectorAll('button'));
                btn = buttons.find(b => /send|发送|验证|获取/i.test(b.textContent));
            }
            const codeInput = document.querySelector('input[autocomplete*="one-time-code"], input[name*="code"], input[placeholder*="code"], input[aria-label*="code"]');
            return {
                phoneInputFound: !!telInput,
                buttonFound: !!btn,
                codeInputFound: !!codeInput
            };
        })()
        """
        
        try:
            det_res = evaluate_js(ws_url, js_detect_phone)
            det = det_res.get("result", {}).get("value", {})
        except Exception:
            continue
            
        if not isinstance(det, dict):
            continue
            
        # 页面显示手机输入框，且当前没有在处理验证码，自动触发 Hero-SMS 最低价购买流程
        if det.get("phoneInputFound") and not det.get("codeInputFound") and sms_state == "idle":
            print(f"\n{C_YELLOW}[BLOCKED] [BLOCKED] 检测到 OpenAI 手机验证短信防御机制！自动拦截并介入！{C_END}")
            sms_state = "testing"
            
            cheapest_countries = get_cheapest_countries()
            if not cheapest_countries:
                print(f"{C_RED}[ERROR] 无法从 Hero-SMS 获取国家列表，重试中...{C_END}")
                sms_state = "idle"
                continue
                
            print(f"[SEARCH] 已自动完成最便宜的号段库存和价格分析，共 {len(cheapest_countries)} 个国家有货。")
            current_country_index = 0
            
        # 执行租号与注入
        if sms_state == "testing":
            if current_country_index >= len(cheapest_countries):
                print(f"{C_RED}[ERROR] 已经测试了所有可供购买的便宜国家，均未成功。{C_END}")
                sms_state = "idle"
                continue
                
            country_info = cheapest_countries[current_country_index]
            cid = country_info["country_id"]
            price = country_info["price"]
            print(f"\n[租号] 正在尝试最便宜的第 {current_country_index + 1} 个国家段 | ID: {cid} | 价格: {price} 卢布...")
            
            rent_info = rent_number(cid)
            if not rent_info or isinstance(rent_info, str):
                print(f"[WARN] 该国家租用失败 ({rent_info})，自动顺延到下一个...")
                current_country_index += 1
                continue
                
            active_activation_id = rent_info["id"]
            phone = rent_info["number"]
            print(f"[PHONE] 成功买入虚拟号！电话: +{phone} (订单ID: {active_activation_id})")
            
            # 使用 JS 将手机号自动填入输入框，并触发 change/input 事件，模拟用户点击发送
            js_fill_phone = f"""
            (function() {{
                const telInput = document.querySelector('input[type="tel"], input[autocomplete*="tel"], input[name*="phone"], input[aria-label*="phone"]');
                if (telInput) {{
                    telInput.value = "+{phone}";
                    telInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    telInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    
                    const buttons = Array.from(document.querySelectorAll('button'));
                    let btn = buttons.find(b => /send|发送|验证|获取/i.test(b.textContent));
                    if (btn) {{
                        btn.click();
                        return true;
                    }}
                }}
                return false;
            }})()
            """
            
            fill_success = evaluate_js(ws_url, js_fill_phone).get("result", {}).get("value", False)
            if fill_success:
                print(f"{C_GREEN}[OK] 已成功在网页中注入号码并自动发送验证码！{C_END}")
                sms_state = "sms_waiting"
                start_wait_time = time.time()
            else:
                print(f"{C_RED}[ERROR] 号码填入网页失败，正在取消订单并顺延...{C_END}")
                set_activation_status(active_activation_id, 8)
                current_country_index += 1
                sms_state = "testing"
                
        # 轮询等待验证码
        if sms_state == "sms_waiting":
            elapsed = int(time.time() - start_wait_time)
            progress = "=" * (elapsed // 5) + " " * ((SMS_TIMEOUT - elapsed) // 5)
            print(f"\r[SEARCH] 正在向 Hero-SMS 查询验证码: [{progress}] {elapsed}/{SMS_TIMEOUT}s", end="")
            
            sms_status = check_sms_status(active_activation_id)
            if "STATUS_OK" in sms_status:
                code = sms_status.split(":")[1]
                print(f"\n{C_GREEN}[SUCCESS] 【成功】已在后台截获验证码: {code}{C_END}")
                
                # 在浏览器输入验证码并提交
                js_fill_code = f"""
                (function() {{
                    const codeInput = document.querySelector('input[autocomplete*="one-time-code"], input[name*="code"], input[placeholder*="code"], input[aria-label*="code"]');
                    if (codeInput) {{
                        codeInput.value = "{code}";
                        codeInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        codeInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        
                        const buttons = Array.from(document.querySelectorAll('button'));
                        let nextBtn = buttons.find(b => /continue|next|提交|继续/i.test(b.textContent));
                        if (nextBtn) {{
                            nextBtn.click();
                        }}
                        return true;
                    }}
                    return false;
                }})()
                """
                evaluate_js(ws_url, js_fill_code)
                print(f"{C_GREEN}[OK] 已自动将验证码填入页面并点击提交！{C_END}")
                
                # 告知平台接码完成，正式扣费
                set_activation_status(active_activation_id, 6)
                sms_state = "idle"
                
            elif "STATUS_WAIT_CODE" in sms_status:
                if elapsed >= SMS_TIMEOUT:
                    print(f"\n[ERROR] 超时！此号码在 {SMS_TIMEOUT} 秒内未能成功接收到验证码。")
                    print("🔄 正在向 API 发送释放并退款请求...")
                    cancel_res = set_activation_status(active_activation_id, 8)
                    print(f"[REFUNDED] 退款响应: {cancel_res}（交易已全额原路取消）")
                    
                    js_go_back = """
                    (function() {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        let backBtn = buttons.find(b => /back|different|返回|其他/i.test(b.textContent));
                        if (backBtn) {
                            backBtn.click();
                            return true;
                        }
                        location.reload();
                        return false;
                    })()
                    """
                    evaluate_js(ws_url, js_go_back)
                    
                    current_country_index += 1
                    sms_state = "testing"
            else:
                print(f"\n[WARN] 状态异常: {sms_status}，重试中...")
                time.sleep(2)

if __name__ == "__main__":
    run_main_flow()
