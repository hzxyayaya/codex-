import os

file_path = r"C:\Users\chengcheng\.gemini\antigravity\scratch\codex-bypass-login\codex_auto_sms_bypass.py"

with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace all problematic unicode emojis and checkmarks with safe ASCII brackets
replacements = {
    "✓": "[OK]",
    "❌": "[ERROR]",
    "⚠️": "[WARN]",
    "🔍": "[SEARCH]",
    "🎉": "[SUCCESS]",
    "🛑": "[BLOCKED]",
    "💸": "[REFUNDED]",
    "⏱️": "[WAIT]",
    "📞": "[PHONE]",
    "👉": "[GUIDE]"
}

for k, v in replacements.items():
    text = text.replace(k, v)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Done cleaning!")
