/**
 * OpenAI Codex Bypass Login - Browser Session Extractor
 * 
 * Instructions:
 * 1. Open your browser and login to https://chatgpt.com/ (your regular ChatGPT account).
 * 2. Press F12 (or Cmd+Option+I on Mac) to open Developer Tools, then click the "Console" tab.
 * 3. Copy this entire script, paste it into the console, and press Enter.
 * 4. It will fetch your session, parse the JWT, configure it for Codex, and copy the JSON payload directly to your clipboard.
 * 5. Run the python/exe companion tool to apply this configuration to your local Codex instance!
 */

(function () {
    console.log("%c[Codex-Bypass]%c Initiating session extraction...", "color: #10a37f; font-weight: bold;", "color: inherit;");

    if (window.location.hostname !== "chatgpt.com") {
        console.error("[Codex-Bypass] Error: This script must be run on https://chatgpt.com/");
        alert("错误：此脚本必须在 https://chatgpt.com/ 域名下运行！\n请先登录 ChatGPT，然后再控制台执行本脚本。");
        return;
    }

    fetch("/api/auth/session")
        .then(async (response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (!data || !data.accessToken) {
                throw new Error("Could not find a valid accessToken in the active session. Are you logged in?");
            }

            const token = data.accessToken;
            let accountId = "";

            // Try to extract account_id from JWT payload
            try {
                const payloadPart = token.split(".")[1];
                const decodedPayload = JSON.parse(atob(payloadPart));
                const authInfo = decodedPayload["https://api.openai.com/auth"] || {};
                accountId = authInfo.chatgpt_account_id || "";
            } catch (err) {
                console.warn("[Codex-Bypass] Warning: Failed to parse account_id from JWT payload:", err);
            }

            // Construct the exact structure expected by OpenAI Codex CLI/Desktop
            // Crucial Trick: We use the access_token as the id_token to satisfy Codex's JWT parsing.
            const authJson = {
                "auth_mode": "chatgpt",
                "OPENAI_API_KEY": null,
                "tokens": {
                    "id_token": token,
                    "access_token": token,
                    "refresh_token": "",
                    "account_id": accountId
                },
                "last_refresh": new Date().toISOString()
            };

            const formattedJson = JSON.stringify(authJson, null, 2);

            // Copy to clipboard
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(formattedJson)
                    .then(() => {
                        showSuccess(formattedJson);
                    })
                    .catch((err) => {
                        console.error("[Codex-Bypass] Clipboard write failed, falling back to legacy copy.", err);
                        fallbackCopy(formattedJson);
                    });
            } else {
                fallbackCopy(formattedJson);
            }
        })
        .catch((err) => {
            console.error("[Codex-Bypass] Extraction failed:", err);
            alert(`获取失败！\n原因: ${err.message}\n请确保您已在网页成功登录 ChatGPT 并且网络正常。`);
        });

    function fallbackCopy(text) {
        try {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.top = "0";
            textArea.style.left = "0";
            textArea.style.width = "2em";
            textArea.style.height = "2em";
            textArea.style.padding = "0";
            textArea.style.border = "none";
            textArea.style.outline = "none";
            textArea.style.boxShadow = "none";
            textArea.style.background = "transparent";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            if (successful) {
                showSuccess(text);
            } else {
                throw new Error("execCommand returned false");
            }
        } catch (err) {
            console.log("[Codex-Bypass] Fallback copy failed:", err);
            promptForCopy(text);
        }
    }

    function promptForCopy(text) {
        console.log("=== COPY THE JSON BELOW ===");
        console.log(text);
        console.log("===========================");
        alert("无法自动复制到剪贴板。请打开控制台(F12)，复制打印出的 JSON 内容，然后运行 Python 辅助工具！");
    }

    function showSuccess(text) {
        console.log("%c[Codex-Bypass]%c SUCCESS! Config JSON copied to clipboard.", "color: #10a37f; font-weight: bold;", "color: #a6e3a1;");
        console.log("=== Config Payload ===");
        console.log(text);
        console.log("======================");
        alert("✓ Token 获取并格式化成功！\n已自动复制到您的剪贴板！\n\n现在请打开终端，运行我们的 Python 辅助工具或双击运行 exe，它会自动检测并应用此配置！");
    }
})();
