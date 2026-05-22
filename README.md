# OpenAI Codex Login Bypass Tool (免手机接码登录辅助工具)

[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)
[![Platform: Windows | macOS | Linux](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-brightgreen.svg)]()

一个简单、免依赖、100% 成功率的 OpenAI Codex (Desktop & CLI) 登录绕过辅助工具。

## 💡 为什么需要这个工具？

在使用 OpenAI Codex 桌面客户端或 CLI 工具进行登录时，OAuth 授权流程默认使用的是 Codex 的官方客户端 ID（`app_EMoamEEZ73f0CkXaXp7hrann`）。
OpenAI 会对使用该客户端 ID 的登录请求强制要求绑定并验证**手机号**，即使你是付费的 **ChatGPT Plus 会员** 也无法直接跳过，从而触发了“手机号码是必填项”的阻碍。

### 🛠️ 绕过原理

1. **共享 Web 端的登录态**：您网页端（`https://chatgpt.com`）的正常登录使用的是 ChatGPT Web 客户端 ID（`app_X8zY6vW2pQ9tR3dE7nK1jL5gH`），该 ID **不强制验证手机号**。
2. **提取并格式化 Session**：我们通过一个简单的浏览器 JavaScript 脚本获取当前网页登录成功后的 `accessToken` (JWT)，并将其组装为 Codex 识别 of 格式。
3. **修复 Codex CLI 崩溃**：为了防止 Codex 内部 Go/Rust 二进制分析器在解析空 `id_token` 时崩溃（提示 `invalid ID token format` 错误），脚本会将 `access_token` 同时写入 `id_token` 字段。
4. **注入本地配置**：最后，将组装好的凭据自动保存到系统本地路径 `~/.codex/auth.json`。此时再次启动 Codex，即可直接跳过授权，实现免验证直接登录。

---

## 🚀 快速使用指南

对于普通用户，我们提供了一键打包好的**一键整合包**，无需安装 Python 环境即可直接使用。

### 第一步：下载一键整合包
1. 进入 GitHub 项目的 [Releases 页面](https://github.com/chengchengking/codex-/releases)。
2. 下载最新的 `codex-bypass-login-v1.0.0.zip` 压缩包。
3. 解压到本地任意文件夹。

### 第二步：在浏览器中登录 ChatGPT
1. 打开您的常用浏览器，访问 [https://chatgpt.com](https://chatgpt.com)。
2. 确保您已处于成功登录状态（能正常和 GPT 对话）。

### 第三步：提取 Session 令牌 (Token)
1. 在当前网页按下 `F12`（或右键 -> 检查）打开开发者工具。
2. 切换到 **Console (控制台)** 面板。
3. 复制并粘贴解压出来的 [codex_session_extractor.js](codex_session_extractor.js) 中的所有代码到控制台中，然后回车运行。
4. **运行结果**：脚本会自动从接口拉取 Token、解析账户 ID 并转换为 Codex 所需的格式，随后**自动复制到您的剪贴板**中。您会看到弹窗提示“✓ Token 获取并格式化成功”。

### 第四步：运行本地辅助工具
1. 双击运行解压出来的 `codex-auth-helper.exe` 辅助工具。
2. 工具会自动检测并读取您剪贴板中刚才从浏览器提取的配置，或者提示您在终端中手动粘贴。
3. 输入 `y` 确认写入配置。配置完成后，工具会调用 `codex.exe login status` 验证，并询问您是否立刻启动 Codex 桌面端，输入 `y` 即可自动拉起。

---

## 📁 仓库文件说明

- [codex_session_extractor.js](codex_session_extractor.js) : 运行于浏览器控制台的 JavaScript 脚本。
- [codex_auth_helper.py](codex_auth_helper.py) : 本地配置写入与验证工具（Python）。
- [build_exe.py](build_exe.py) : 用于将 Python 脚本打包为 Windows 单文件可执行程序并制作 zip 整合包的脚本。
- [requirements.txt](requirements.txt) : Python 运行依赖项。

---

## 🛠️ 二次开发与自行打包

如果您需要自行修改 Python 脚本并重新打包，请遵循以下步骤：

1. 安装依赖项：
   ```bash
   pip install -r requirements.txt
   ```
2. 运行打包脚本：
   ```bash
   python build_exe.py
   ```
3. 打包完成后，您将在当前目录下的 `dist/` 文件夹中找到打包成功的 `codex-auth-helper.exe` 以及一键整合压缩包 `codex-bypass-login-v1.0.0.zip`。

---

## ⚠️ 安全与隐私警示

> [!WARNING]
> 本工具生成的配置包含您 ChatGPT 账号的有效 `access_token`。该 Token 等同于您的临时登录密码，拥有您账号的访问权限。
> 1. **千万不要**将生成的 `auth.json` 包含的 JSON 字符分享给任何人，或将其上传到任何公开网络/GitHub Issue 中！
> 2. 该 Token 的有效期限约为 **10天**，过期后 Codex 将会提示未登录。届时只需重新执行上述步骤，覆盖一次即可。
> 3. 本工具为开源辅助程序，所有代码逻辑均在本地运行，不会将您的任何数据上传到第三方服务器。

---

## 📄 开源许可证

本项目基于 [The Unlicense](LICENSE) 协议发布，完全进入公共领域（Public Domain），任何人可以自由分发、修改、闭源或商用。
