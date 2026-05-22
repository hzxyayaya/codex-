# OpenAI Codex Login Bypass Tool (免手机接码登录辅助工具)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows | macOS | Linux](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-brightgreen.svg)]()

一个简单、免依赖、100% 成功率的 OpenAI Codex (Desktop & CLI) 登录绕过辅助工具。

## 💡 为什么需要这个工具？

在使用 OpenAI Codex 桌面客户端或 CLI 工具进行登录时，OAuth 授权流程默认使用的是 Codex 的官方客户端 ID（`app_EMoamEEZ73f0CkXaXp7hrann`）。
OpenAI 会对使用该客户端 ID 的登录请求强制要求绑定并验证**手机号**，即使你是付费的 **ChatGPT Plus 会员** 也无法直接跳过，从而触发了“手机号码是必填项”的阻碍。

### 🛠️ 绕过原理

1. **共享 Web 端的登录态**：您网页端（`https://chatgpt.com`）的正常登录使用的是 ChatGPT Web 客户端 ID（`app_X8zY6vW2pQ9tR3dE7nK1jL5gH`），该 ID **不强制验证手机号**。
2. **提取并格式化 Session**：我们通过一个简单的浏览器 JavaScript 脚本获取当前网页登录成功后的 `accessToken` (JWT)，并将其组装为 Codex 识别的格式。
3. **修复 Codex CLI 崩溃**：为了防止 Codex 内部 Go/Rust 二进制分析器在解析空 `id_token` 时崩溃（提示 `invalid ID token format` 错误），脚本会将 `access_token` 同时写入 `id_token` 字段。
4. **注入本地配置**：最后，将组装好的凭据自动保存到系统本地路径 `~/.codex/auth.json`。此时再次启动 Codex，即可直接跳过授权，实现免验证直接登录。

---

## 🚀 快速使用指南

只需要三步，即可完成登录绕过：

### 第一步：在浏览器中登录 ChatGPT
1. 打开您的常用浏览器，访问 [https://chatgpt.com](https://chatgpt.com)。
2. 确保您已处于成功登录状态（能正常和 GPT 对话）。

### 第二步：提取 Session 令牌 (Token)
1. 在当前网页按下 `F12`（或右键 -> 检查）打开开发者工具。
2. 切换到 **Console (控制台)** 面板。
3. 复制并粘贴 [codex_session_extractor.js](codex_session_extractor.js) 中的所有代码到控制台中，然后回车运行。
4. **运行结果**：脚本会自动从接口拉取 Token、解析账户 ID 并转换为 Codex 所需的格式，随后**自动复制到您的剪贴板**中。您会看到弹窗提示“✓ Token 获取并格式化成功”。

### 第三步：运行本地辅助工具
你可以选择使用 **Python 脚本** 运行，或者在 Windows 上直接运行**打包好的 `.exe` 文件**：

#### 选项 A：使用打包好的可执行程序 (Windows 无需安装 Python)
1. 从 Release 中下载并运行 `codex-auth-helper.exe`。
2. 运行后，工具会自动检测并读取您剪贴板中刚才提取的内容。
3. 输入 `y` 确认应用配置。
4. 配置写入完成后，程序会使用 `codex.exe login status` 验证，并询问您是否立刻启动 Codex 桌面客户端，输入 `y` 即可自动拉起。

#### 选项 B：使用 Python 脚本运行
1. 安装剪贴板支持依赖（可选，不安装也可手动粘贴）：
   ```bash
   pip install pyperclip
   ```
2. 运行辅助脚本：
   ```bash
   python codex_auth_helper.py
   ```
3. 脚本会自动读取您的剪贴板（或引导您手动在终端中右键粘贴），自动完成备份与覆盖，并帮您完成登录状态验证与拉起客户端。

---

## 📁 仓库文件说明

- [codex_session_extractor.js](codex_session_extractor.js) : 运行于浏览器控制台的 JavaScript 脚本。
- [codex_auth_helper.py](codex_auth_helper.py) : 本地配置写入与验证工具（Python）。
- [build_exe.py](build_exe.py) : 用于将 Python 脚本打包为 Windows 单文件可执行程序的脚本。
- [requirements.txt](requirements.txt) : Python 运行依赖项。

---

## 🛠️ 二次开发与自行打包

如果您需要自行修改 Python 脚本并重新打包为 `.exe` 文件，请遵循以下步骤：

1. 安装依赖项：
   ```bash
   pip install -r requirements.txt
   ```
2. 运行打包脚本：
   ```bash
   python build_exe.py
   ```
3. 打包完成后，您将在当前目录下的 `dist/` 文件夹中找到打包成功的 `codex-auth-helper.exe` 可执行程序。

---

## ⚠️ 安全与隐私警示

> [!WARNING]
> 本工具生成的配置包含您 ChatGPT 账号的有效 `access_token`。该 Token 等同于您的临时登录密码，拥有您账号的访问权限。
> 1. **千万不要**将生成的 `auth.json` 包含的 JSON 字符分享给任何人，或将其上传到任何公开网络/GitHub Issue 中！
> 2. 该 Token 的有效期限约为 **10天**，过期后 Codex 将会提示未登录。届时只需重新执行上述步骤，覆盖一次即可。
> 3. 本工具为开源辅助程序，所有代码逻辑均在本地运行，不会将您的任何数据上传到第三方服务器。

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。
