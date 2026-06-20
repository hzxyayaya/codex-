# PowerShell Codex Auth Sync Helper
# Native, lightweight replacement for the compiled .exe file.
# Scans browsers, retrieves ChatGPT session, and syncs via Cloudflare Worker.

$ErrorActionPreference = "Stop"

# Force console to output UTF-8 to avoid encoding issues
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Show-Banner {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "       OpenAI Codex Login Bypass Companion Tool (PS Version)" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "    Bypassing phone/SMS verification using Cloud authorization" -ForegroundColor Gray
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Scan-Browsers {
    $browsers = New-Object System.Collections.Generic.List[PSObject]
    
    # 1. Check registry on Windows
    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        $regKeysToCheck = @(
            @("Google Chrome", "chrome.exe"),
            @("Microsoft Edge", "msedge.exe"),
            @("360安全浏览器", "360se.exe"),
            @("360极速浏览器", "360chrome.exe"),
            @("QQ浏览器", "qqbrowser.exe"),
            @("Brave Browser", "brave.exe"),
            @("Opera Browser", "opera.exe"),
            @("Vivaldi Browser", "vivaldi.exe")
        )
        
        foreach ($item in $regKeysToCheck) {
            $name = $item[0]
            $exe = $item[1]
            $path = "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\$exe"
            
            foreach ($hive in @("HKLM", "HKCU")) {
                $regKey = "${hive}:\$path"
                if (Test-Path $regKey) {
                    try {
                        $val = (Get-ItemProperty -Path $regKey -Name "")."(default)"
                        if ($val) {
                            $cleanPath = $val.Trim().Trim('"').Trim("'").Trim()
                            if ($cleanPath -and (Test-Path $cleanPath)) {
                                $browsers.Add([PSCustomObject]@{ Name = $name; Path = $cleanPath })
                                break
                            }
                        }
                    } catch {}
                }
            }
        }
    }
    
    # 2. Check fallback standard paths
    $fallbacks = @(
        @("Google Chrome", "D:\Program Files\Google\Chrome\Application\chrome.exe"),
        @("Google Chrome", "D:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        @("Google Chrome", "C:\Program Files\Google\Chrome\Application\chrome.exe"),
        @("Google Chrome", "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        @("Google Chrome", "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"),
        
        @("Microsoft Edge", "D:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        @("Microsoft Edge", "D:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        @("Microsoft Edge", "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        @("Microsoft Edge", "C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        @("Microsoft Edge", "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe"),
        
        @("360安全浏览器", "C:\Program Files (x86)\360\360se6\Application\360se.exe"),
        @("360安全浏览器", "C:\Program Files\360\360se6\Application\360se.exe"),
        @("360安全浏览器", "$env:APPDATA\360se6\Application\360se.exe"),
        
        @("360极速浏览器", "C:\Program Files (x86)\360\360chrome\Application\360chrome.exe"),
        @("360极速浏览器", "C:\Program Files\360\360chrome\Application\360chrome.exe"),
        @("360极速浏览器", "$env:LOCALAPPDATA\360Chrome\Chrome\Application\360chrome.exe"),
        
        @("QQ浏览器", "C:\Program Files (x86)\Tencent\QQBrowser\QQBrowser.exe"),
        @("QQ浏览器", "C:\Program Files\Tencent\QQBrowser\QQBrowser.exe"),
        @("QQ浏览器", "$env:LOCALAPPDATA\Tencent\QQBrowser\Application\QQBrowser.exe")
    )
    
    $foundNames = $browsers | ForEach-Object { $_.Name }
    foreach ($item in $fallbacks) {
        $name = $item[0]
        $path = $item[1]
        if ($name -notin $foundNames -and $path -and (Test-Path $path)) {
            $browsers.Add([PSCustomObject]@{ Name = $name; Path = $path })
            $foundNames += $name
        }
    }
    
    return $browsers
}

function Evaluate-JS {
    param(
        [string]$wsUrl,
        [string]$expression
    )
    
    $uri = [System.Uri]$wsUrl
    $port = if ($uri.Port -eq -1) { 80 } else { $uri.Port }
    
    $client = New-Object System.Net.Sockets.TcpClient($uri.Host, $port)
    $stream = $client.GetStream()
    
    # WebSocket Handshake
    $key = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("dGhlIHNhbXBsZSBub25jZQ=="))
    $handshake = "GET $($uri.PathAndQuery) HTTP/1.1`r`n" +
                 "Host: $($uri.Host)`r`n" +
                 "Upgrade: websocket`r`n" +
                 "Connection: Upgrade`r`n" +
                 "Sec-WebSocket-Key: $key`r`n" +
                 "Sec-WebSocket-Version: 13`r`n`r`n"
                 
    $handshakeBytes = [Text.Encoding]::ASCII.GetBytes($handshake)
    $stream.Write($handshakeBytes, 0, $handshakeBytes.Length)
    
    $buffer = New-Object byte[] 4096
    $bytesRead = $stream.Read($buffer, 0, $buffer.Length)
    $response = [Text.Encoding]::ASCII.GetString($buffer, 0, $bytesRead)
    if ($response -notmatch "101 Switching Protocols") {
        $client.Close()
        throw "WebSocket Handshake failed"
    }
    
    # Send Runtime.evaluate command
    $cmdObj = @{
        id = 1
        method = "Runtime.evaluate"
        params = @{
            expression = $expression
            awaitPromise = $true
            returnByValue = $true
        }
    }
    $cmdJson = $cmdObj | ConvertTo-Json -Compress
    $payloadBytes = [Text.Encoding]::UTF8.GetBytes($cmdJson)
    $len = $payloadBytes.Length
    
    $frame = New-Object System.Collections.Generic.List[byte]
    $frame.Add(0x81) # Text frame, FIN
    
    if ($len -le 125) {
        $frame.Add($len -bor 0x80) # Masked (client -> server MUST mask)
    } elseif ($len -le 65535) {
        $frame.Add(126 -bor 0x80)
        $frame.Add(($len -shr 8) -band 0xff)
        $frame.Add($len -band 0xff)
    }
    
    # Mask key
    $mask = @(0x01, 0x02, 0x03, 0x04)
    $frame.AddRange($mask)
    
    # Mask payload
    for ($i = 0; $i -lt $len; $i++) {
        $frame.Add($payloadBytes[$i] -bxor $mask[$i % 4])
    }
    
    $frameBytes = $frame.ToArray()
    $stream.Write($frameBytes, 0, $frameBytes.Length)
    
    # Read response
    $dataList = New-Object System.Collections.Generic.List[byte]
    $bytesRead = $stream.Read($buffer, 0, $buffer.Length)
    $dataList.AddRange($buffer[0..($bytesRead-1)])
    
    while ($dataList.Count -lt 2) {
        $bytesRead = $stream.Read($buffer, 0, $buffer.Length)
        $dataList.AddRange($buffer[0..($bytesRead-1)])
    }
    
    $payloadLen = $dataList[1] -band 0x7f
    $offset = 2
    if ($payloadLen -eq 126) {
        while ($dataList.Count -lt 4) {
            $bytesRead = $stream.Read($buffer, 0, $buffer.Length)
            $dataList.AddRange($buffer[0..($bytesRead-1)])
        }
        $payloadLen = ($dataList[2] -shl 8) + $dataList[3]
        $offset = 4
    }
    
    while ($dataList.Count -lt ($offset + $payloadLen)) {
        $bytesRead = $stream.Read($buffer, 0, $buffer.Length)
        $dataList.AddRange($buffer[0..($bytesRead-1)])
    }
    
    $client.Close()
    
    $payloadBytes = $dataList.ToArray()[$offset..($offset + $payloadLen - 1)]
    $resJson = [Text.Encoding]::UTF8.GetString($payloadBytes)
    return $resJson | ConvertFrom-Json
}

function Extract-AccountId {
    param([string]$token)
    try {
        $parts = $token.Split('.')
        if ($parts.Length -eq 3) {
            $payloadB64 = $parts[1]
            $padding = 4 - ($payloadB64.Length % 4)
            if ($padding -ne 4) {
                $payloadB64 += "=" * $padding
            }
            # Replace URL-safe base64 chars
            $payloadB64 = $payloadB64.Replace('-', '+').Replace('_', '/')
            $bytes = [Convert]::FromBase64String($payloadB64)
            $payloadStr = [Text.Encoding]::UTF8.GetString($bytes)
            $payload = $payloadStr | ConvertFrom-Json
            return $payload."https://api.openai.com/auth".chatgpt_account_id
        }
    } catch {}
    return ""
}

function Check-ExistingSession {
    param(
        [string]$browserPath,
        [string]$userDir,
        [int]$port
    )
    
    $args = @(
        "--remote-debugging-port=$port",
        "--user-data-dir=$userDir",
        "--no-first-run",
        "--no-default-browser-check",
        "--headless",
        "https://chatgpt.com/"
    )
    
    $proc = Start-Process -FilePath $browserPath -ArgumentList $args -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2
    
    $wsUrl = $null
    for ($i = 0; $i -lt 5; $i++) {
        try {
            $targets = Invoke-RestMethod -Uri "http://127.0.0.1:$port/json" -UseBasicParsing
            foreach ($t in $targets) {
                if ($t.type -eq "page" -and $t.url -like "*chatgpt.com*") {
                    $wsUrl = $t.webSocketDebuggerUrl
                    break
                }
            }
            if ($wsUrl) { break }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    
    $token = $null
    if ($wsUrl) {
        $js = "fetch('/api/auth/session').then(r=>r.json()).then(d=>d.accessToken?{success:true,t:d.accessToken}:{success:false}).catch(e=>{success:false})"
        try {
            $res = Evaluate-JS -wsUrl $wsUrl -expression $js
            $val = $res.result.result.value
            if ($val.success) {
                $token = $val.t
            }
        } catch {}
    }
    
    # Terminate process
    try {
        $proc | Stop-Process -Force -ErrorAction SilentlyContinue
    } catch {}
    
    return $token
}

function Run-LoginBypass {
    param($authData)
    
    $codexDir = Join-Path $env:USERPROFILE ".codex"
    if (-not (Test-Path $codexDir)) {
        New-Item -ItemType Directory -Path $codexDir -Force | Out-Null
    }
    
    $authFile = Join-Path $codexDir "auth.json"
    
    # Backup existing auth.json
    if (Test-Path $authFile) {
        $timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
        $bakFile = Join-Path $codexDir "auth.json.bak_$timestamp"
        Rename-Item -Path $authFile -NewName (Split-Path $bakFile -Leaf) -Force
    }
    
    # Save authData
    $authData | ConvertTo-Json -Depth 5 | Out-File -FilePath $authFile -Encoding utf8 -Force
    Write-Host "[OK] 配置成功写入至: $authFile" -ForegroundColor Green
    
    # Apply local config.toml optimization based on plan type
    try {
        $planType = "free"
        $accessToken = $authData.tokens.access_token
        $parts = $accessToken.Split('.')
        if ($parts.Length -eq 3) {
            $payloadB64 = $parts[1]
            $padding = 4 - ($payloadB64.Length % 4)
            if ($padding -ne 4) { $payloadB64 += "=" * $padding }
            $payloadB64 = $payloadB64.Replace('-', '+').Replace('_', '/')
            $bytes = [Convert]::FromBase64String($payloadB64)
            $payload = ([Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json)
            $planType = $payload."https://api.openai.com/auth".chatgpt_plan_type
        }
        
        $configPath = Join-Path $codexDir "config.toml"
        if (Test-Path $configPath) {
            $lines = Get-Content $configPath
            $newLines = @()
            foreach ($line in $lines) {
                if ($line.Trim() -like "model =*") {
                    if ($planType -eq "free") { $newLines += 'model = "gpt-5-codex-mini"' }
                    else { $newLines += 'model = "gpt-5.5"' }
                } elseif ($line.Trim() -like "model_reasoning_effort =*") {
                    if ($planType -eq "free") { $newLines += 'model_reasoning_effort = "low"' }
                    else { $newLines += 'model_reasoning_effort = "xhigh"' }
                } else {
                    $newLines += $line
                }
            }
            $newLines | Out-File $configPath -Encoding utf8 -Force
            Write-Host "[自适应优化] 检测到您的账户为 $planType 订阅，已自动优化 config.toml！" -ForegroundColor Gray
        }
    } catch {
        Write-Host "[自适应警告] 自动优化 config.toml 失败: $_" -ForegroundColor Yellow
    }
}

function Locate-CodexBin {
    $paths = @(
        Join-Path $env:USERPROFILE "AppData\Local\OpenAI\Codex\bin\codex.exe"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Graft-With-Cloudflare {
    param(
        $token,
        $accountId,
        $workerUrl
    )
    
    $graftUrl = "$workerUrl/graft"
    $headers = @{
        "Content-Type" = "application/json"
        "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    $payload = @{
        access_token = $token
        account_id = $accountId
    } | ConvertTo-Json -Compress
    
    Write-Host "[授权嫁接] 正在通过云端免验证服务嫁接凭证..." -ForegroundColor Gray
    try {
        $graftedAuthData = Invoke-RestMethod -Uri $graftUrl -Headers $headers -Method Post -Body $payload -UseBasicParsing
        return $graftedAuthData
    } catch {
        Write-Host "[错误] 凭证嫁接失败: $_" -ForegroundColor Red
        Exit 1
    }
}

# Main Execution Flow
Clear-Host
Show-Banner

Write-Host "正在为您启动一键免验证登录获取流程..." -ForegroundColor Gray

# 1. Scan for browsers
$browsers = Scan-Browsers
if ($browsers.Count -eq 0) {
    Write-Error "错误：未在您的电脑中检测到安装的 Chrome 或 Edge 浏览器。"
    Exit 1
}

Write-Host ""
Write-Host "[系统扫描] 检测到您电脑中安装了以下浏览器：" -ForegroundColor Gray
for ($i = 0; $i -lt $browsers.Count; $i++) {
    Write-Host "  [$($i + 1)] $($browsers[$i].Name) (安装路径: $($browsers[$i].Path))" -ForegroundColor Gray
}

$choice = 0
if ($browsers.Count -gt 1) {
    while ($true) {
        $ans = (Read-Host "`n请选择您已登录 ChatGPT 的浏览器序号 (1-$($browsers.Count)) [默认 1]").Trim()
        if (-not $ans) {
            $choice = 0
            break
        }
        if ($ans -as [int]) {
            $idx = [int]$ans - 1
            if ($idx -ge 0 -and $idx -lt $browsers.Count) {
                $choice = $idx
                break
            }
        }
        Write-Host "输入错误：请输入 1 到 $($browsers.Count) 之间的有效数字。" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n系统仅检测到单个支持的浏览器，将自动使用: $($browsers[0].Name)" -ForegroundColor Gray
}

$browserName = $browsers[$choice].Name
$browserPath = $browsers[$choice].Path
Write-Host "已选择并绑定浏览器: $browserName" -ForegroundColor Green

$port = 9333
$userDir = Join-Path $env:USERPROFILE ".codex\browser_session"

# 2. Check for existing active session
Write-Host "`n[自动获取] 正在检查当前浏览器会话的登录状态..." -ForegroundColor Gray
$token = Check-ExistingSession -browserPath $browserPath -userDir $userDir -port $port

if (-not $token) {
    # 3. Not logged in, launch browser in foreground
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host " 【第一步】请在弹出的浏览器窗口中登录您的 ChatGPT 账号。 (支持 Plus 套餐)" -ForegroundColor Yellow
    Write-Host " 【第二步】登录成功并进入聊天界面（确保页面能正常聊天）后，" -ForegroundColor Yellow
    Write-Host "          请直接【手动关闭该浏览器窗口】！本工具将自动提取 Token！" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Yellow
    
    $args = @(
        "--user-data-dir=$userDir",
        "--no-first-run",
        "--no-default-browser-check",
        "https://chatgpt.com/"
    )
    $proc = Start-Process -FilePath $browserPath -ArgumentList $args -PassThru
    $proc.WaitForExit()
    
    Write-Host "`n[自动获取] 检测到浏览器已关闭。正在重新启动后台服务以提取 Token..." -ForegroundColor Gray
    
    # 4. Launch debugger in background to extract
    $argsDebug = @(
        "--remote-debugging-port=$port",
        "--user-data-dir=$userDir",
        "--no-first-run",
        "--no-default-browser-check",
        "--headless",
        "https://chatgpt.com/"
    )
    $procDebug = Start-Process -FilePath $browserPath -ArgumentList $argsDebug -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2
    
    $wsUrl = $null
    for ($i = 0; $i -lt 10; $i++) {
        try {
            $targets = Invoke-RestMethod -Uri "http://127.0.0.1:$port/json" -UseBasicParsing
            foreach ($t in $targets) {
                if ($t.type -eq "page" -and $t.url -like "*chatgpt.com*") {
                    $wsUrl = $t.webSocketDebuggerUrl
                    break
                }
            }
            if ($wsUrl) { break }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    
    if ($wsUrl) {
        $js = "fetch('/api/auth/session').then(r=>r.json()).then(d=>d.accessToken?{success:true,t:d.accessToken}:{success:false}).catch(e=>{success:false})"
        try {
            $res = Evaluate-JS -wsUrl $wsUrl -expression $js
            $val = $res.result.result.value
            if ($val.success) {
                $token = $val.t
                Write-Host "[自动获取] ✓ 成功获取 Token！" -ForegroundColor Green
            }
        } catch {}
    }
    
    try {
        $procDebug | Stop-Process -Force -ErrorAction SilentlyContinue
    } catch {}
}

if (-not $token) {
    Write-Error "[错误] 无法获取您的登录凭证，请确保已在浏览器窗口中登录 ChatGPT 并成功进入聊天页面。"
    Exit 1
}

# 5. Extract account ID
$accountId = Extract-AccountId -token $token

# 6. Graft via Cloudflare Worker statelessly (Zero-config & Zero-key)
$workerUrl = "https://codex-sync-worker.epidemicsituation.workers.dev"
$graftedAuthData = Graft-With-Cloudflare -token $token -accountId $accountId -workerUrl $workerUrl

# 7. Write config
Run-LoginBypass -authData $graftedAuthData

# 9. Launch Codex
$codexPath = Locate-CodexBin
if ($codexPath) {
    Write-Host ""
    $ans = (Read-Host "是否现在启动 Codex 桌面应用？(Y/n)").Trim().ToLower()
    if ($ans -eq "y" -or $ans -eq "yes" -or -not $ans) {
        Write-Host "[启动] 正在启动 Codex..." -ForegroundColor Gray
        Start-Process -FilePath $codexPath -ArgumentList "app"
        Write-Host "[成功] Codex 桌面进程已启动。祝您使用愉快！" -ForegroundColor Green
    }
} else {
    Write-Host "`n[提示] 凭证已更新成功！未找到默认安装路径的 Codex，您可以手动启动客户端。" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "         同步流程已全部结束，本窗口 3 秒后自动关闭" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Start-Sleep -Seconds 3
