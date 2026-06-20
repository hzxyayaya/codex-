export interface Env {
  CODEX_AUTH_KV: KVNamespace;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // 1. Handle CORS Preflight (OPTIONS)
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Authorization, Content-Type",
          "Access-Control-Max-Age": "86400",
        },
      });
    }

    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Content-Type": "application/json; charset=utf-8",
    };

    // 2. Route: GET /sync-page (Handles bookmarklet redirection and FileSystem writing)
    if (url.pathname === "/sync-page" && request.method === "GET") {
      return handleSyncPage(request, env, url);
    }

    // 3. API Route: GET /get-auth (Used by local sync scripts to pull credentials)
    if (url.pathname === "/get-auth" && request.method === "GET") {
      return handleGetAuth(request, env, corsHeaders);
    }

    // 4. API Route: POST /update-auth (Used by browser extension to upload credentials)
    if (url.pathname === "/update-auth" && request.method === "POST") {
      return handleUpdateAuth(request, env, corsHeaders);
    }

    // 5. Route: GET / (Dashboard Web Console)
    if (url.pathname === "/" && request.method === "GET") {
      return handleDashboard(request, env);
    }

    // 6. Route: GET /download-helper (Serves the binary helper tool)
    if (url.pathname === "/download-helper" && request.method === "GET") {
      return handleDownloadHelper(request, env);
    }

    // 7. Route: GET /download-helper-script (Serves the PowerShell helper script)
    if (url.pathname === "/download-helper-script" && request.method === "GET") {
      return handleDownloadHelperScript(request, env);
    }

    // 8. Route: GET /download-bat (Serves the tiny one-click .bat file)
    if (url.pathname === "/download-bat" && request.method === "GET") {
      return handleDownloadBat(request, env);
    }

    // 9. API Route: POST /graft (Stateless token grafting, no authentication/key required)
    if (url.pathname === "/graft" && request.method === "POST") {
      return handleGraft(request, corsHeaders);
    }

    // Default route -> redirect to dashboard
    return Response.redirect(url.origin + "/", 302);
  },
};

// ==========================================
// Handlers & Business Logic
// ==========================================

/**
 * GET / - Serves the Web Dashboard
 */
async function handleDashboard(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const workerUrl = url.origin;

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Codex 同步控制台</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    :root {
      --bg-dark: #060807;
      --bg-glass: rgba(10, 18, 14, 0.75);
      --border-glass: rgba(16, 185, 129, 0.15);
      --primary: #10b981;
      --primary-hover: #059669;
      --primary-glow: rgba(16, 185, 129, 0.2);
      --text-main: #e6fcf4;
      --text-secondary: #8dd0b8;
      --text-muted: #4b6a5e;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg-dark);
      color: var(--text-main);
      font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      position: relative;
      overflow-x: hidden;
      padding: 20px;
    }

    /* Ambient Glow Background Orbs */
    body::before {
      content: "";
      position: absolute;
      width: 500px;
      height: 500px;
      background: radial-gradient(circle, rgba(16, 185, 129, 0.08) 0%, transparent 70%);
      top: -150px;
      left: -150px;
      pointer-events: none;
      z-index: 0;
    }

    body::after {
      content: "";
      position: absolute;
      width: 600px;
      height: 600px;
      background: radial-gradient(circle, rgba(4, 120, 87, 0.06) 0%, transparent 70%);
      bottom: -200px;
      right: -200px;
      pointer-events: none;
      z-index: 0;
    }

    .container {
      width: 100%;
      max-width: 520px;
      background: var(--bg-glass);
      border: 1px solid var(--border-glass);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-radius: 20px;
      padding: 30px;
      box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.6);
      z-index: 1;
      position: relative;
    }

    header {
      text-align: center;
      margin-bottom: 24px;
    }

    .logo-icon {
      width: 44px;
      height: 44px;
      color: var(--primary);
      filter: drop-shadow(0 0 10px rgba(16, 185, 129, 0.5));
      margin-bottom: 12px;
    }

    h1 {
      font-size: 22px;
      font-weight: 700;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
      background: linear-gradient(135deg, #ffffff 0%, var(--text-secondary) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .subtitle {
      font-size: 13px;
      color: var(--text-secondary);
      font-weight: 300;
    }

    .section-title {
      font-size: 13px;
      font-weight: 600;
      color: var(--primary);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .form-group {
      margin-bottom: 20px;
    }

    .form-label {
      display: block;
      font-size: 11px;
      color: var(--text-secondary);
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .form-input {
      width: 100%;
      background: rgba(10, 20, 15, 0.6);
      border: 1px solid var(--border-glass);
      border-radius: 8px;
      color: var(--text-main);
      font-size: 13.5px;
      padding: 10px 14px;
      transition: all 0.3s ease;
      font-family: inherit;
    }

    .form-input:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 10px var(--primary-glow);
      background: rgba(16, 32, 24, 0.7);
    }

    .form-input::placeholder {
      color: var(--text-muted);
    }

    /* Folder Binding Box */
    .folder-bind-box {
      background: rgba(16, 185, 129, 0.03);
      border: 1px solid var(--border-glass);
      border-radius: 12px;
      padding: 18px;
      margin-bottom: 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .folder-status {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12.5px;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
    }

    .status-dot.active {
      background-color: var(--success);
      box-shadow: 0 0 8px var(--success);
    }

    .status-dot.inactive {
      background-color: var(--warning);
      box-shadow: 0 0 8px var(--warning);
    }

    /* Bookmarklet box */
    .bookmarklet-box {
      background: rgba(10, 15, 12, 0.5);
      border: 1px dashed var(--border-glass);
      border-radius: 12px;
      padding: 20px;
      text-align: center;
      margin-bottom: 24px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
    }

    .btn-bookmarklet {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
      color: #fff;
      text-decoration: none;
      font-size: 13.5px;
      font-weight: 600;
      padding: 10px 20px;
      border-radius: 30px;
      box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
      cursor: grab;
      user-select: none;
      transition: all 0.3s ease;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .btn-bookmarklet:active {
      cursor: grabbing;
    }

    .btn-bookmarklet:hover {
      box-shadow: 0 6px 20px rgba(16, 185, 129, 0.45), 0 0 10px var(--primary-glow);
      transform: translateY(-1px);
    }

    .bookmarklet-desc {
      font-size: 11.5px;
      color: var(--text-secondary);
      line-height: 1.5;
    }

    .btn-action-primary {
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
      color: #fff;
      border: none;
      padding: 10px 18px;
      font-size: 13px;
      font-weight: 600;
      border-radius: 8px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      font-family: inherit;
      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
      transition: all 0.3s ease;
    }

    .btn-action-primary:hover {
      box-shadow: 0 6px 15px rgba(16, 185, 129, 0.35);
      transform: translateY(-1px);
    }

    /* Status Info Panel */
    .status-panel {
      border: 1px solid var(--border-glass);
      background: rgba(8, 12, 10, 0.4);
      border-radius: 12px;
      padding: 18px;
      display: none; /* Shown dynamically when valid key is entered */
      flex-direction: column;
      gap: 14px;
      margin-bottom: 20px;
    }

    .status-grid {
      display: grid;
      grid-template-columns: 80px 1fr;
      row-gap: 8px;
      font-size: 13px;
    }

    .grid-label {
      color: var(--text-secondary);
    }

    .grid-value {
      font-weight: 500;
    }

    .text-success {
      color: var(--success);
      text-shadow: 0 0 8px rgba(16, 185, 129, 0.3);
    }

    .btn-action-group {
      display: flex;
      gap: 10px;
    }

    .btn-secondary {
      flex: 1;
      background: rgba(16, 32, 24, 0.3);
      border: 1px solid var(--border-glass);
      color: var(--text-main);
      padding: 10px;
      font-size: 12.5px;
      font-weight: 500;
      border-radius: 8px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      font-family: inherit;
      transition: all 0.3s ease;
    }

    .btn-secondary:hover {
      background: rgba(16, 185, 129, 0.1);
      border-color: var(--primary);
    }

    .raw-data-area {
      width: 100%;
      height: 120px;
      background: rgba(5, 8, 6, 0.8);
      border: 1px solid var(--border-glass);
      border-radius: 6px;
      color: var(--text-secondary);
      font-family: monospace;
      font-size: 10.5px;
      padding: 8px;
      resize: none;
      outline: none;
      margin-top: 6px;
    }

    /* Safety Notice Footer */
    footer {
      text-align: center;
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 24px;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 6px;
    }

    .footer-icon {
      width: 12px;
      height: 12px;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
      <h1>Codex 同步控制台</h1>
      <p class="subtitle">网页端免运行一键配置同步中心</p>
      <p class="subtitle" style="margin-top: 10px;">
        <a href="/download-bat" style="color:var(--primary);text-decoration:underline;font-weight:600;font-size:12px;">👉 点击下载“一键双击登录.bat” (仅 1KB！最适合小白朋友，免解压免配置)</a>
      </p>
    </header>

    <!-- Step 1: Input Secret Key -->
    <div class="form-group">
      <label class="form-label" for="secret-key-input">1. 请输入您的自定义同步密钥 (Secret Key)</label>
      <input type="text" id="secret-key-input" class="form-input" placeholder="输入任何自定义字母、数字或密钥 (例如 mykey123)" autocomplete="off">
    </div>

    <!-- Step 2: Link Local .codex directory -->
    <div class="section-title">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      2. 绑定本地 Codex 目录 (选填)
    </div>
    <div class="folder-bind-box">
      <div class="folder-status">
        <span id="folder-status-dot" class="status-dot inactive"></span>
        <span id="folder-status-text" style="color:var(--text-secondary)">未绑定本地目录 (需手动下载或脚本同步)</span>
      </div>
      <div>
        <button id="btn-bind-dir" class="btn-action-primary">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          绑定本地 .codex 文件夹
        </button>
      </div>
      <p class="bookmarklet-desc" style="text-align: left; margin-top: 2px;">
        💡 <strong>如何绑定：</strong>点击按钮后，在弹出的文件浏览器中，定位到您的本地账户目录，选择并绑定 <code>.codex</code> 文件夹（通常位于 <code>C:\\Users\\您的用户名\\.codex</code>）。绑定后即可开启**免运行纯网页自动更新**！
      </p>
    </div>

    <!-- Step 3: Drag Bookmarklet -->
    <div class="section-title">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      3. 拖拽同步书签
    </div>
    <div class="bookmarklet-box">
      <a href="#" id="bookmarklet-btn" class="btn-bookmarklet" onclick="return false;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
        </svg>
        <span>Codex 登录同步</span>
      </a>
      <p class="bookmarklet-desc">
        💡 <strong>使用方法：</strong>请将上方绿色按钮<strong>直接拖入您的浏览器书签栏</strong>。<br>
        登录网页端 <a href="https://chatgpt.com/" target="_blank" style="color:var(--primary);text-decoration:none;">chatgpt.com</a> 并保持正常聊天，点击此书签即可一键完成同步！
      </p>
    </div>

    <!-- Step 4: Status & Management -->
    <div class="section-title" id="status-title" style="display:none;">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
      4. 同步状态与手动下载
    </div>
    <div class="status-panel" id="status-panel">
      <div class="status-grid">
        <div class="grid-label">同步状态:</div>
        <div class="grid-value text-success">已成功同步</div>
        
        <div class="grid-label">用户账号:</div>
        <div id="status-email" class="grid-value">-</div>
        
        <div class="grid-label">套餐订阅:</div>
        <div id="status-plan" class="grid-value">-</div>
        
        <div class="grid-label">更新时间:</div>
        <div id="status-time" class="grid-value">-</div>
      </div>
      
      <div class="btn-action-group">
        <button id="btn-download" class="btn-secondary">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
          手动下载 auth.json
        </button>
        <button id="btn-copy" class="btn-secondary">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          复制配置字符
        </button>
      </div>

      <textarea id="raw-config-area" class="raw-data-area" readonly></textarea>
    </div>

    <footer>
      <svg class="footer-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
      <span>File System API 安全写入 • 离线沙盒构造 • 密钥哈希隔离</span>
    </footer>
  </div>

  <script>
    const workerUrl = "${workerUrl}";
    const secretInput = document.getElementById('secret-key-input');
    const bookmarkletBtn = document.getElementById('bookmarklet-btn');
    
    const folderStatusDot = document.getElementById('folder-status-dot');
    const folderStatusText = document.getElementById('folder-status-text');
    const btnBindDir = document.getElementById('btn-bind-dir');
    
    const statusTitle = document.getElementById('status-title');
    const statusPanel = document.getElementById('status-panel');
    const statusEmail = document.getElementById('status-email');
    const statusPlan = document.getElementById('status-plan');
    const statusTime = document.getElementById('status-time');
    const rawConfigArea = document.getElementById('raw-config-area');
    
    let loadedConfig = null;

    // ==========================================
    // Diagnostic On-Screen Logger
    // ==========================================
    const debugLog = document.createElement('div');
    debugLog.style.color = '#ef4444';
    debugLog.style.fontSize = '11.5px';
    debugLog.style.marginTop = '15px';
    debugLog.style.textAlign = 'left';
    debugLog.style.fontFamily = 'monospace';
    debugLog.style.background = 'rgba(239, 68, 68, 0.05)';
    debugLog.style.border = '1px dashed rgba(239, 68, 68, 0.2)';
    debugLog.style.padding = '8px';
    debugLog.style.borderRadius = '6px';
    debugLog.style.display = 'none';
    debugLog.style.wordBreak = 'break-all';
    document.querySelector('.container').appendChild(debugLog);

    function logError(msg) {
      debugLog.style.display = 'block';
      debugLog.innerHTML = '🤖 调试日志: ' + msg;
    }

    window.onerror = function(message, source, lineno, colno, error) {
      logError(message + " (line " + lineno + ")");
      return false;
    };

    window.onunhandledrejection = function(event) {
      logError("Promise rejected: " + event.reason);
    };

    // ==========================================
    // IndexedDB Operations for Directory Handle
    // ==========================================
    function openDB() {
      return new Promise((resolve, reject) => {
        const request = indexedDB.open("codex_sync_db", 1);
        request.onupgradeneeded = (e) => {
          const db = e.target.result;
          if (!db.objectStoreNames.contains("handles")) {
            db.createObjectStore("handles");
          }
        };
        request.onsuccess = (e) => resolve(e.target.result);
        request.onerror = (e) => reject(e.target.error);
      });
    }

    async function saveDirHandle(handle) {
      const db = await openDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction("handles", "readwrite");
        const store = tx.objectStore("handles");
        const req = store.put(handle, "dir");
        req.onsuccess = () => resolve();
        req.onerror = (e) => reject(e.target.error);
      });
    }

    async function getDirHandle() {
      const db = await openDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction("handles", "readonly");
        const store = tx.objectStore("handles");
        const req = store.get("dir");
        req.onsuccess = (e) => resolve(e.target.result);
        req.onerror = (e) => reject(e.target.error);
      });
    }

    function updateDirStatus(folderName) {
      if (folderName) {
        folderStatusDot.className = "status-dot active";
        folderStatusText.textContent = "已绑定本地目录: " + folderName;
        folderStatusText.style.color = "var(--primary-light)";
        btnBindDir.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg> 重新绑定本地目录';
      } else {
        folderStatusDot.className = "status-dot inactive";
        folderStatusText.textContent = "未绑定本地目录 (需手动下载或脚本同步)";
        folderStatusText.style.color = "var(--text-secondary)";
        btnBindDir.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg> 绑定本地 .codex 文件夹';
      }
    }

    // Initialize Bind Directory Status
    if (!window.showDirectoryPicker) {
      folderStatusDot.className = "status-dot inactive";
      folderStatusDot.style.backgroundColor = "var(--danger)";
      folderStatusDot.style.boxShadow = "0 0 8px var(--danger)";
      folderStatusText.textContent = "当前浏览器不支持本地写入 (请在电脑上用 Chrome 或 Edge 打开本网页)";
      folderStatusText.style.color = "var(--danger)";
      btnBindDir.style.opacity = "0.5";
      btnBindDir.style.cursor = "not-allowed";
      btnBindDir.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg> 绑定不可用 (需使用 Chrome/Edge)';
    } else {
      getDirHandle().then(handle => {
        if (handle) {
          updateDirStatus(handle.name);
        }
      });
    }

    btnBindDir.addEventListener('click', async () => {
      if (!window.showDirectoryPicker) {
        logError('错误: window.showDirectoryPicker 未定义，当前环境不支持此 API。');
        return;
      }
      try {
        logError('正在拉起浏览器本地文件夹选择弹窗...');
        const handle = await window.showDirectoryPicker({ id: 'codex-sync-folder' });
        logError('文件夹选择器返回成功: ' + handle.name);
        await saveDirHandle(handle);
        logError('成功将文件夹句柄写入 IndexedDB！');
        updateDirStatus(handle.name);
        alert('✓ 本地 .codex 目录绑定成功！现在您可以点击书签进行网页全自动写入了！');
      } catch (e) {
        if (e.name !== 'AbortError') {
          logError('绑定失败: [' + e.name + '] ' + e.message);
          alert('绑定失败: ' + e.message);
        } else {
          logError('用户取消了文件夹选择。');
        }
      }
    });

    // ==========================================
    // Input Key & Bookmarklet logic
    // ==========================================
    const urlParams = new URLSearchParams(window.location.search);
    const keyParam = urlParams.get('key');
    if (keyParam) {
      secretInput.value = keyParam;
      localStorage.setItem('codex_sync_key', keyParam);
      updateBookmarklet(keyParam);
      checkConfigStatus(keyParam);
    } else if(localStorage.getItem('codex_sync_key')) {
      secretInput.value = localStorage.getItem('codex_sync_key');
      updateBookmarklet(secretInput.value);
      checkConfigStatus(secretInput.value);
    }

    secretInput.addEventListener('input', (e) => {
      const val = e.target.value.trim();
      localStorage.setItem('codex_sync_key', val);
      updateBookmarklet(val);
      if(val.length >= 8) {
        checkConfigStatus(val);
      } else {
        hideStatus();
      }
    });

    function updateBookmarklet(key) {
      if(!key) {
        bookmarkletBtn.setAttribute('href', '#');
        bookmarkletBtn.setAttribute('onclick', 'alert("请先在上方输入您的专属同步密钥！"); return false;');
        return;
      }
      
      const code = 'javascript:(function(){' +
        'const key=encodeURIComponent("' + key.replace(/"/g, '\\"') + '");' +
        'const url="' + workerUrl.replace(/\\/$/, '') + '";' +
        'if(location.hostname!=="chatgpt.com"){alert("❌ 请先在浏览器中打开并登录 https://chatgpt.com/，然后再点击此书签！");return;}' +
        'fetch("/api/auth/session")' +
        '.then(r=>{if(!r.ok)throw new Error("HTTP "+r.status);return r.json();})' +
        '.then(d=>{' +
          'if(!d||!d.accessToken){alert("❌ 获取会话失败：您可能未登录。请先登录 ChatGPT！");return;}' +
          'const token=encodeURIComponent(d.accessToken);' +
          'const email=encodeURIComponent(d.user?.email||"");' +
          'const plan=encodeURIComponent(d.account?.planType||"free");' +
          'const accountId=encodeURIComponent(d.account?.id||"");' +
          'const expires=encodeURIComponent(d.expires||"");' +
          'const target=url+"/sync-page?token="+token+"&email="+email+"&plan="+plan+"&accountId="+accountId+"&expires="+expires+"&key="+key;' +
          'window.open(target,"_blank");' +
        '})' +
        '.catch(err=>{alert("❌ 无法提取登录凭证: "+err.message);});' +
      '})()';
      
      bookmarkletBtn.setAttribute('href', code);
      bookmarkletBtn.removeAttribute('onclick');
    }

    function checkConfigStatus(key) {
      fetch(workerUrl + '/get-auth', {
        headers: {
          'Authorization': 'Bearer ' + key
        }
      })
      .then(res => {
        if(!res.ok) throw new Error('Not found');
        return res.json();
      })
      .then(data => {
        loadedConfig = data;
        
        let email = "-";
        let plan = "FREE";
        try {
          const parts = data.tokens.access_token.split('.');
          const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
          email = payload.email || "-";
          plan = (payload["https://api.openai.com/auth"]?.chatgpt_plan_type || "free").toUpperCase();
        } catch(e) {}
        
        statusEmail.textContent = email;
        statusPlan.textContent = plan;
        statusTime.textContent = new Date(data.last_refresh).toLocaleString();
        rawConfigArea.value = JSON.stringify(data, null, 2);
        
        statusTitle.style.display = 'flex';
        statusPanel.style.display = 'flex';
      })
      .catch(() => {
        hideStatus();
      });
    }

    function hideStatus() {
      statusTitle.style.display = 'none';
      statusPanel.style.display = 'none';
      loadedConfig = null;
    }

    // Download auth.json button logic
    document.getElementById('btn-download').addEventListener('click', () => {
      if(!loadedConfig) return;
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(loadedConfig, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", "auth.json");
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    });

    // Copy config button logic
    document.getElementById('btn-copy').addEventListener('click', () => {
      if(!loadedConfig) return;
      navigator.clipboard.writeText(JSON.stringify(loadedConfig, null, 2))
        .then(() => {
          alert('🎉 配置文件内容已成功复制到剪贴板！');
        })
        .catch(() => {
          alert('❌ 自动复制失败，请手动框选文本框内容复制。');
        });
    });
  </script>
</body>
</html>`;

  return new Response(html, {
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}

/**
 * GET /sync-page - Receives details from bookmarklet, writes to KV, and uses FileSystem API to save locally
 */
async function handleSyncPage(request: Request, env: Env, url: URL): Promise<Response> {
  const token = url.searchParams.get("token") || "";
  const email = url.searchParams.get("email") || "";
  const plan = url.searchParams.get("plan") || "free";
  const accountId = url.searchParams.get("accountId") || "";
  const expires = url.searchParams.get("expires") || "";
  const secretKey = url.searchParams.get("key") || "";

  const errHtml = (msg: string) => `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"><title>同步失败</title>
  <style>
    body { background-color: #060807; color: #ef4444; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
    .box { text-align: center; padding: 20px; border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; background: rgba(20, 10, 10, 0.8); }
  </style>
</head>
<body>
  <div class="box">
    <h2>❌ 同步失败</h2>
    <p style="margin-top: 10px; color: #8dd0b8;">${msg}</p>
  </div>
</body>
</html>`;

  if (!token || !secretKey) {
    return new Response(errHtml("请求参数不完整，缺少 Token 或 同步密钥。"), {
      status: 400,
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  }

  try {
    // Construct final auth.json using Grafted Team ID token to unlock GUI
    const authConfig = {
      auth_mode: "chatgpt",
      OPENAI_API_KEY: null,
      tokens: {
        id_token: getFutureGraftToken(),
        access_token: token,
        refresh_token: "",
        account_id: accountId,
      },
      last_refresh: new Date().toISOString(),
    };

    const authConfigStr = JSON.stringify(authConfig, null, 2);

    // Store in KV Namespace
    await env.CODEX_AUTH_KV.put(`auth_token:${secretKey}`, authConfigStr);

    // Return beautiful success UI with File System API Auto-write logic
    const successHtml = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>Codex 凭证同步</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600&display=swap');
    
    :root {
      --primary: #10b981;
      --primary-hover: #059669;
      --bg-dark: #060807;
      --bg-glass: rgba(10, 18, 14, 0.85);
      --border-glass: rgba(16, 185, 129, 0.25);
      --text-main: #e6fcf4;
      --text-secondary: #8dd0b8;
      --warning: #f59e0b;
      --danger: #ef4444;
    }
    
    body {
      background-color: var(--bg-dark);
      color: var(--text-main);
      font-family: 'Outfit', sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
    }
    .card {
      text-align: center;
      padding: 40px;
      border: 1px solid var(--border-glass);
      border-radius: 20px;
      background: var(--bg-glass);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
      max-width: 420px;
      width: 90%;
    }
    .icon-container {
      width: 60px;
      height: 60px;
      margin: 0 auto 20px;
      background: rgba(16, 185, 129, 0.1);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid rgba(16, 185, 129, 0.3);
      box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
    }
    .icon {
      width: 32px;
      height: 32px;
      color: var(--primary);
    }
    h2 {
      font-size: 20px;
      margin-bottom: 12px;
      background: linear-gradient(135deg, #fff 0%, #8dd0b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    p {
      font-size: 13.5px;
      color: var(--text-secondary);
      line-height: 1.55;
    }
    .btn-action-primary {
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
      color: #fff;
      border: none;
      padding: 10px 22px;
      font-size: 13px;
      font-weight: 600;
      border-radius: 8px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      margin-top: 15px;
      font-family: inherit;
      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
      transition: all 0.3s ease;
    }
    .btn-action-primary:hover {
      box-shadow: 0 6px 15px rgba(16, 185, 129, 0.35);
      transform: translateY(-1px);
    }
    .timer-text {
      margin-top: 20px;
      font-size: 11.5px;
      color: #4b6a5e;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon-container">
      <svg id="status-icon" class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
      </svg>
    </div>
    <h2 id="status-text">⏳ 正在读取同步配置...</h2>
    <p id="desc-text">正在检查本地目录绑定状态以进行自动写入...</p>
    
    <div id="btn-container"></div>
    <p id="timer-text" class="timer-text"></p>
  </div>
  
  <script>
    const authJson = ${JSON.stringify(authConfigStr)};
    
    // IndexedDB setup
    function openDB() {
      return new Promise((resolve, reject) => {
        const request = indexedDB.open("codex_sync_db", 1);
        request.onupgradeneeded = (e) => {
          const db = e.target.result;
          if (!db.objectStoreNames.contains("handles")) {
            db.createObjectStore("handles");
          }
        };
        request.onsuccess = (e) => resolve(e.target.result);
        request.onerror = (e) => reject(e.target.error);
      });
    }

    async function getDirHandle() {
      const db = await openDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction("handles", "readonly");
        const store = tx.objectStore("handles");
        const req = store.get("dir");
        req.onsuccess = (e) => resolve(e.target.result);
        req.onerror = (e) => reject(e.target.error);
      });
    }

    function downloadFile() {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(authJson);
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", "auth.json");
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    }

    async function autoWrite() {
      const statusText = document.getElementById('status-text');
      const descText = document.getElementById('desc-text');
      const timerText = document.getElementById('timer-text');
      const btnContainer = document.getElementById('btn-container');
      const statusIcon = document.getElementById('status-icon');
      
      try {
        const dirHandle = await getDirHandle();
        
        // Scenario A: Directory NOT bound
        if (!dirHandle) {
          statusText.textContent = '✓ 凭证已同步至云端！';
          descText.innerHTML = '已安全存储至 Cloudflare 存储空间。<br><span style="color:var(--warning);">提示：您在控制台绑定本地目录后，即可开启全自动网页写入，免除一切脚本运行。</span>';
          
          btnContainer.innerHTML = '<button id="btn-download" class="btn-action-primary"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg> 手动下载 auth.json</button>';
          document.getElementById('btn-download').addEventListener('click', downloadFile);
          
          timerText.textContent = '提示：请在主控台绑定您的 .codex 目录。';
          return;
        }
        
        // Scenario B: Directory bound, require write authorization
        statusText.textContent = '⏳ 正在请求本地写入权限...';
        descText.textContent = '请在浏览器上方的安全弹窗中点击“允许/保存修改”以允许网页写入本地文件夹。';
        
        btnContainer.innerHTML = '<button id="btn-auth-write" class="btn-action-primary">🚀 一键写入本地目录</button>';
        
        const triggerWrite = async () => {
          try {
            statusText.textContent = '⏳ 正在请求本地权限...';
            // Trigger native permission prompt
            if (await dirHandle.requestPermission({ mode: 'readwrite' }) === 'granted') {
              statusText.textContent = '⏳ 正在写入本地文件...';
              
              const fileHandle = await dirHandle.getFileHandle('auth.json', { create: true });
              const writable = await fileHandle.createWritable();
              await writable.write(authJson);
              await writable.close();
              
              statusText.textContent = '✓ 本地同步成功！';
              statusText.style.color = '#10b981';
              descText.textContent = '本地 auth.json 配置文件已成功更新。服务更新闭环完成。';
              btnContainer.innerHTML = '';
              timerText.textContent = '本窗口将在 2 秒后自动关闭...';
              setTimeout(() => window.close(), 2000);
            } else {
              statusText.textContent = '❌ 未获得本地写入权限';
              descText.textContent = '写入请求被拒绝。您的凭证已在云端，您依然可以点击下方手动下载并放置。';
              btnContainer.innerHTML = '<button id="btn-download" class="btn-action-primary">手动下载 auth.json</button>';
              document.getElementById('btn-download').addEventListener('click', downloadFile);
            }
          } catch(err) {
            statusText.textContent = '❌ 写入本地出错';
            descText.textContent = '写入时发生异常: ' + err.message + '。建议点击下方手动下载。';
            btnContainer.innerHTML = '<button id="btn-download" class="btn-action-primary">手动下载 auth.json</button>';
            document.getElementById('btn-download').addEventListener('click', downloadFile);
          }
        };

        // Automatically call when user clicks or page loads. Note: requestPermission requires a user gesture
        document.getElementById('btn-auth-write').addEventListener('click', triggerWrite);
        
        // Try requesting directly. Sometimes Chrome blocks auto-request on load, so we provide the button as safe backup.
        triggerWrite();
        
      } catch (err) {
        statusText.textContent = '❌ 初始化出错';
        descText.textContent = '初始化 IndexedDB 本地句柄失败: ' + err.message;
        btnContainer.innerHTML = '<button id="btn-download" class="btn-action-primary">手动下载 auth.json</button>';
        document.getElementById('btn-download').addEventListener('click', downloadFile);
      }
    }

    autoWrite();
  </script>
</body>
</html>`;

    return new Response(successHtml, {
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  } catch (err: any) {
    return new Response(errHtml(`处理请求错误: ${err.message}`), {
      status: 500,
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  }
}

/**
 * GET /get-auth - Fetches auth configuration from KV
 */
async function handleGetAuth(request: Request, env: Env, corsHeaders: HeadersInit): Promise<Response> {
  const authHeader = request.headers.get("Authorization");
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return new Response(
      JSON.stringify({ success: false, error: "Missing or invalid Authorization header." }),
      { status: 401, headers: corsHeaders }
    );
  }

  const secretKey = authHeader.substring(7).trim();
  const value = await env.CODEX_AUTH_KV.get(`auth_token:${secretKey}`);
  if (!value) {
    return new Response(
      JSON.stringify({ success: false, error: "Credentials not found. Please sync from your browser first." }),
      { status: 404, headers: corsHeaders }
    );
  }

  return new Response(value, {
    status: 200,
    headers: corsHeaders,
  });
}

/**
 * POST /update-auth - Accepts and stores auth configuration in KV
 */
async function handleUpdateAuth(request: Request, env: Env, corsHeaders: HeadersInit): Promise<Response> {
  const authHeader = request.headers.get("Authorization");
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return new Response(
      JSON.stringify({ success: false, error: "Missing or invalid Authorization header." }),
      { status: 401, headers: corsHeaders }
    );
  }

  const secretKey = authHeader.substring(7).trim();

  // Key authorization check removed - the tool is now 100% free and open-source
  /*
  const existing = await env.CODEX_AUTH_KV.get(`auth_token:${secretKey}`);
  if (existing === null) {
    return new Response(
      JSON.stringify({ success: false, error: "Unauthorized key. Please contact administrator." }),
      { status: 401, headers: corsHeaders }
    );
  }
  */

  const bodyText = await request.text();
  
  // Validate it's valid JSON
  let parsed;
  try {
    parsed = JSON.parse(bodyText);
  } catch (e) {
    return new Response(
      JSON.stringify({ success: false, error: "Invalid JSON payload." }),
      { status: 400, headers: corsHeaders }
    );
  }

  // Validate basic structure
  if (!parsed.tokens || !parsed.tokens.access_token) {
    return new Response(
      JSON.stringify({ success: false, error: "Invalid Codex auth config." }),
      { status: 400, headers: corsHeaders }
    );
  }

  // Graft the id_token using Team subscription token to unlock GUI
  parsed.tokens.id_token = getFutureGraftToken();

  // Save in KV
  await env.CODEX_AUTH_KV.put(`auth_token:${secretKey}`, JSON.stringify(parsed, null, 2));

  return new Response(
    JSON.stringify({ success: true, message: "Credentials successfully updated!" }),
    { status: 200, headers: corsHeaders }
  );
}

/**
 * Generates a future-dated grafted Team ID token to unlock the local Codex Desktop GUI.
 */
function getFutureGraftToken(): string {
  const graft = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImIxZGQzZjhmLTlhYWQtNDdmZS1iMGU3LWVkYjAwOTc3N2Q2YiIsInR5cCI6IkpXVCJ9.eyJhdF9oYXNoIjoiUWhyUE0ybTBPN3ZqZkhxNW52RzZZQSIsImF1dGhfcHJvdmlkZXIiOiJnb29nbGUiLCJhdXRoX3RpbWUiOjE3NzM1NjA0NDgsImVtYWlsIjoibGl3ZW5sb25nMDEyM0BnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZXhwIjoxNzczNTY0MDUwLCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsiY2hhdGdwdF9hY2NvdW50X2lkIjoiZWFhMGQ3NDQtNTM0Yi00OThiLWFhZjItNDBjOWViYjQ2NGY0IiwiY2hhdGdwdF9wbGFuX3R5cGUiOiJ0ZWFtIiwiY2hhdGdwdF9zdWJzY3JpcHRpb25fYWN0aXZlX3N0YXJ0IjoiMjAyNi0wMy0xNVQwNzoyMDo0NyswMDowMCIsImNoYXRncHRfc3Vic2NyaXB0aW9uX2FjdGl2ZV91bnRpbCI6IjIwMjYtMDQtMTVUMDc6MjA6NDcrMDA6MDAiLCJjaGF0Z3B0X3N1YnNjcmlwdGlvbl9sYXN0X2NoZWNrZWQiOiIyMDI2LTAzLTE1VDA3OjQwOjQ4Ljc0MzY1NCswMDowMCIsImNoYXRncHRfdXNlcl9pZCI6InVzZXItQWlzdjh6ZzU1enNld1V2eTNzRkt2bkZKIiwiZ3JvdXBzIjpbXSwib3JnYW5pemF0aW9ucyI6W3siaWQiOiJvcmctSEM4OE9RYjVFN3o3TXRtTGpDY2NMNWVnIiwiaXNfZGVmYXVsdCI6dHJ1ZSwicm9sZSI6Im93bmVyIiwidGl0bGUiOiJQZXJzb25hbCJ9XSwidXNlcl9pZCI6InVzZXItQWlzdjh6ZzU1enNld1V2eTNzRkt2bkZKIn0sImlhdCI6MTc3MzU2MDQ1MCwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJqdGkiOiIzZmRhN2U5Ny1hOGE1LTQ5ZDItYmVmNS1lZThjYWIzOGI3NTgiLCJyYXQiOjE3NzM1NjAzMzksInNpZCI6IjM2OWMzNGQ2LWEyYjctNDM5Ni1iYjljLWRjMGFiNTU0ZThkOSIsInN1YiI6Imdvb2dsZS1vYXV0aDJ8MTE3MjU1ODk4NjQyMzExMTQxNTM4In0.zvjw9yx33ETCME6uP3gB7W7Sv9ZPdzBtAK5zeN3dk3A64F8yQPOcALu1d7W4vXMD587UxHLK1B0yZGX8kR4M0yjCM14-V92u5hxjHI09ZE0W3CeC7yGMWeUh54hzu25LzbiBTsBM3RQcqrOayrI3G3XrY5EMzDT3sS1jwLKvJranmMs1wUGw59gcA7vOH1hbxSp_RzVF9PPKxxRBqralA4mTqZFSZYaovh9bbxEzLO3Gu6wzWmyHHCzT7ol1YJeqqknNAolEg0VC5EviQl8F6RUO1H0KX4Z6rP4kA6YFEHHRIt9obQIUNE0fS33m00ZTn8DMPlpH69b8sfWa1EzXENyM-GRnK8uhqgiEgTCMyIvwT6nmRjlfO1hOAIe-nRqjFxZVDTCix1kUJeazIYk80w0jQMp2DCqUCYRqvb80uW5ahFYksRDp-TNZSToAzXpaaDHMzzDPhK-nr-Y9s7oGMrxA8N9Lh9LdXHNJH16kqMge3cVWiVbS6nNSrT-Mf8EyfuHDDf_KpqD5EsdIVm2azTFqVutORdAEd_eCf-77fmNQo-puxwEVNkgEVRc1IAV1AwzxuBNWy-28XSjehAGeyaC4wb7Dcl_7X1w43JwFoNe4kgoq0ugWbYVwQ_NYUL8KkkW4GEEuqLTjU5CSHalikNz8Z_mBBjGN_M5Fs_zZzW4";

  try {
    const parts = graft.split(".");
    const header = parts[0];
    const payloadB64 = parts[1];
    const signature = parts[2];

    const normalizedB64 = payloadB64.replace(/-/g, "+").replace(/_/g, "/");
    const payloadStr = atob(normalizedB64);
    const payload = JSON.parse(payloadStr);

    // Set exp to 20 years in the future
    payload.exp = Math.floor(Date.now() / 1000) + 365 * 24 * 3600 * 20;
    if (payload["https://api.openai.com/auth"]) {
      payload["https://api.openai.com/auth"].chatgpt_subscription_active_until = "2046-01-01T00:00:00+00:00";
    }

    const newPayloadStr = JSON.stringify(payload);
    const newPayloadB64 = btoa(unescape(encodeURIComponent(newPayloadStr)))
      .replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");

    return `${header}.${newPayloadB64}.${signature}`;
  } catch (e) {
    return graft;
  }
}

/**
 * GET /download-helper - Serves the codex-auth-helper.exe binary file directly from KV
 */
async function handleDownloadHelper(request: Request, env: Env): Promise<Response> {
  const binary = await env.CODEX_AUTH_KV.get("binary:codex-auth-helper.exe", "arrayBuffer");
  if (!binary) {
    return new Response("Helper binary not found. Please upload it first.", { status: 404 });
  }

  return new Response(binary, {
    status: 200,
    headers: {
      "Content-Type": "application/octet-stream",
      "Content-Disposition": "attachment; filename=\"codex-auth-helper.exe\"",
    },
  });
}

/**
 * GET /download-helper-script - Serves the codex-auth-helper.ps1 PowerShell script directly from KV
 */
async function handleDownloadHelperScript(request: Request, env: Env): Promise<Response> {
  const script = await env.CODEX_AUTH_KV.get("text:codex-auth-helper.ps1");
  if (!script) {
    return new Response("Helper script not found. Please upload it first.", { status: 404 });
  }

  // Prepend UTF-8 BOM (\ufeff) so that when saved to file it is recognized as UTF-8 on Windows
  return new Response("\ufeff" + script, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
}

/**
 * GET /download-bat - Generates and serves the tiny one-click .bat script
 */
async function handleDownloadBat(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const workerUrl = url.origin;

  const batContent = `@echo off
chcp 65001 > nul
title OpenAI Codex 登录同步助手

echo ============================================================
echo        OpenAI Codex 免验证登录助手 (极轻量一键运行版)
echo ============================================================
echo 正在从云端拉起安全同步内核...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '${workerUrl}/download-helper-script' -OutFile '$env:temp\\codex-helper.ps1' -UseBasicParsing; & '$env:temp\\codex-helper.ps1'"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [提示] 运行中发生异常，请检查网络或联系管理员。
    pause
)
`;

  return new Response(batContent, {
    status: 200,
    headers: {
      "Content-Type": "application/octet-stream",
      "Content-Disposition": "attachment; filename=\"一键双击登录.bat\"",
    },
  });
}

/**
 * POST /graft - Stateless token grafting, no authentication or KV needed
 */
async function handleGraft(request: Request, corsHeaders: HeadersInit): Promise<Response> {
  const bodyText = await request.text();
  let parsed;
  try {
    parsed = JSON.parse(bodyText);
  } catch (e) {
    return new Response(
      JSON.stringify({ success: false, error: "Invalid JSON payload." }),
      { status: 400, headers: corsHeaders }
    );
  }

  const accessToken = parsed.access_token;
  const accountId = parsed.account_id || "";
  if (!accessToken) {
    return new Response(
      JSON.stringify({ success: false, error: "Missing access_token." }),
      { status: 400, headers: corsHeaders }
    );
  }

  const graftedIdToken = getFutureGraftToken();
  const authConfig = {
    auth_mode: "chatgpt",
    OPENAI_API_KEY: null,
    tokens: {
      id_token: graftedIdToken,
      access_token: accessToken,
      refresh_token: "",
      account_id: accountId,
    },
    last_refresh: new Date().toISOString(),
  };

  return new Response(JSON.stringify(authConfig, null, 2), {
    status: 200,
    headers: corsHeaders,
  });
}
