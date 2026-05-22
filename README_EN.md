# OpenAI Codex Login Bypass Tool

[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)
[![Platform: Windows | macOS | Linux](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-brightgreen.svg)]()

A simple, zero-dependency, 100% success-rate login bypass utility for OpenAI Codex Desktop & CLI.

## 💡 Why is this tool needed?

When logging into the OpenAI Codex desktop client or CLI, the OAuth login process uses the official Codex client ID (`app_EMoamEEZ73f0CkXaXp7hrann`).
OpenAI enforces **phone number / SMS verification** specifically for requests originating from this client ID. Even if you are a paying **ChatGPT Plus subscriber**, you cannot bypass this screen, which blocks users from logging in without a valid phone number.

### 🛠️ Bypass Principle

1. **Shared Web Session**: Your standard browser login on `https://chatgpt.com` uses the ChatGPT Web client ID (`app_X8zY6vW2pQ9tR3dE7nK1jL5gH`), which **does not** require phone verification.
2. **Extract & Format Session**: We run a simple JavaScript script in the browser console to fetch your active `accessToken` (JWT) and structure it into the format Codex expects.
3. **Fix Codex CLI Crashes**: To prevent Codex's underlying Go/Rust binary from crashing with an `invalid ID token format` error when parsing an empty `id_token`, our script automatically duplicates the `access_token` into the `id_token` field.
4. **Inject Configuration**: The formatted credentials are saved to `~/.codex/auth.json`. Codex reads this local configuration on launch and immediately bypasses the login/phone verification flow.

---

## 🚀 Quick Start Guide

For regular users, we provide a **One-Click Integration Package** (ZIP file) so you can get started immediately without setting up a Python environment.

### Step 1: Download the Package
1. Navigate to the GitHub project's [Releases Page](https://github.com/chengchengking/codex-/releases).
2. Download the latest `codex-bypass-login-v1.0.0.zip` archive.
3. Extract it to any local folder on your computer.

### Step 2: Log in to ChatGPT in your Browser
1. Go to your browser and log into [https://chatgpt.com](https://chatgpt.com).
2. Ensure you are fully logged in and can chat with GPT.

### Step 3: Extract your Session Token
1. On the ChatGPT page, press `F12` (or right-click and choose **Inspect**) to open Developer Tools.
2. Navigate to the **Console** tab.
3. Copy the entire code from the extracted [codex_session_extractor.js](codex_session_extractor.js), paste it into the console, and press **Enter**.
4. **Result**: The script will automatically fetch your session, parse the account ID, structure the Codex payload, and **copy it to your clipboard**. You will see an alert: "✓ Token successfully retrieved and formatted".

### Step 4: Run the Local Helper Tool
1. Double-click the extracted `codex-auth-helper.exe` utility.
2. The tool will automatically detect and read the Codex configuration JSON from your clipboard, or guide you to paste it in the terminal manually.
3. Confirm by entering `y`. Once done, it will verify the login status via `codex.exe login status` and ask if you want to start Codex Desktop. Enter `y` to launch.

---

## 📁 Repository Structure

- [codex_session_extractor.js](codex_session_extractor.js): The JavaScript extractor run in the browser console.
- [codex_auth_helper.py](codex_auth_helper.py): The Python desktop companion script.
- [build_exe.py](build_exe.py): The build automation script to package the helper script into a standalone `.exe` executable and create the release ZIP archive.
- [requirements.txt](requirements.txt): List of Python package dependencies.

---

## 🛠️ Development & Compiling

To modify the Python script and compile it into a standalone executable:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute the build script:
   ```bash
   python build_exe.py
   ```
3. Once completed, your executable and ZIP archive will be located in the `dist/` directory as `codex-auth-helper.exe` and `codex-bypass-login-v1.0.0.zip`.

---

## ⚠️ Security & Privacy Warning

> [!WARNING]
> The generated configuration JSON contains a valid `access_token` for your ChatGPT account. This token acts as a temporary password and grants access to your profile.
> 1. **DO NOT** share this JSON payload or access token with anyone, and never post it in public issues, chats, or repositories!
> 2. The token is typically valid for **10 days**. When it expires and Codex asks you to log in again, simply rerun the extractor script to refresh your local configuration.
> 3. This tool runs entirely on your local machine; none of your credentials are ever transmitted to third-party servers.

---

## 📄 License

This project is released under [The Unlicense](LICENSE), dedicating all copyright interest to the public domain. You are free to copy, modify, publish, distribute, or compile this software for commercial or non-commercial purposes.
