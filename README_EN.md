# OpenAI Codex Login Bypass Tool

A simple, zero-dependency, 100% success-rate login bypass utility for OpenAI Codex Desktop.

## 💡 Why is this tool needed?

When logging into the OpenAI Codex desktop client, the standard OAuth flow requires phone number (SMS) verification.
This tool extracts your active session token from the browser (which does not require phone verification) and statelessly grafts a permanent Team ID token via Cloudflare Worker, writing the valid credentials directly into `~/.codex/auth.json` to bypass verification completely.

---

## 🚀 One-Click Key-Free Startup

We have removed all compiled `.exe` files and eliminated the need for any sync password or `Secret Key`. The codebase is 100% open-source, lightweight, and works out-of-the-box.

### Usage Instructions

1. **Download the Repository**:
   - Download the code files in this repository to your local drive.
2. **Double-Click to Launch**:
   - Double-click [双击运行.bat](双击运行.bat).
3. **Automatic Extraction**:
   - The script scans your local Chrome or Edge browsers and opens an isolated browser login window.
   - Log in to your ChatGPT account. Once you see the chat interface working, **close the browser window manually**.
   - The tool will automatically capture the token, send it to the Cloudflare Worker `/graft` endpoint, and save the result locally.
4. **Launch Codex**:
   - Once success is shown, launch the Codex Desktop client as instructed!

---

## 📁 File Structure

- [双击运行.bat](双击运行.bat): One-click startup batch script for Windows.
- [codex-auth-helper.ps1](codex-auth-helper.ps1): Open-source PowerShell sync script.
- [codex_session_extractor.js](codex_session_extractor.js): Backup JavaScript code for manual token extraction in the browser console.
- [cloudflare-worker/](cloudflare-worker/): Cloudflare Worker server-side stateless source code.

---

## ⚠️ Security & Privacy

1. This project **does not collect or store** any of your tokens. The Cloudflare Worker `/graft` route is completely stateless. It performs string manipulation on the JWT in memory and immediately sends it back without database or KV storage.
2. The `access_token` is generally valid for **10 days**. Rerun this tool once it expires.
3. You can deploy your own instance of the Cloudflare Worker server using the source code provided in [cloudflare-worker/](cloudflare-worker/).

---

## 📄 License

Dedicated to the public domain under [The Unlicense](LICENSE).
