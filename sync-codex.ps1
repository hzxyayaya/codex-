# PowerShell Codex Sync Script
# Pulls Codex credentials from Cloudflare Worker and updates local configuration.

$ScriptDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
$ConfigFile = Join-Path $ScriptDir "sync-config.json"

# 1. Load or initialize configuration
if (Test-Path $ConfigFile) {
    try {
        $Config = Get-Content -Raw $ConfigFile | ConvertFrom-Json
        $WorkerUrl = $Config.WorkerUrl
        $SecretKey = $Config.SecretKey
    } catch {
        Write-Host "Warning: Failed to parse sync-config.json, re-initializing..." -ForegroundColor Yellow
    }
}

if (-not $WorkerUrl -or -not $SecretKey) {
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host "   Codex Cloudflare Sync Initial Setup" -ForegroundColor Cyan
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host "This script will save your settings locally in sync-config.json." -ForegroundColor Gray
    
    $WorkerUrl = Read-Host "Enter your Cloudflare Worker URL (e.g., https://your-worker.workers.dev)"
    $WorkerUrl = $WorkerUrl.Trim().TrimEnd('/')
    
    $SecretKey = Read-Host "Enter your Sync Secret Key"
    $SecretKey = $SecretKey.Trim()
    
    if (-not $WorkerUrl -or -not $SecretKey) {
        Write-Error "Error: Worker URL and Secret Key cannot be empty."
        Exit 1
    }
    
    $ConfigObj = @{
        WorkerUrl = $WorkerUrl
        SecretKey = $SecretKey
    }
    
    $ConfigObj | ConvertTo-Json | Out-File -FilePath $ConfigFile -Encoding utf8 -Force
    Write-Host "✓ Settings saved to sync-config.json" -ForegroundColor Green
    Write-Host ""
}

# 2. Perform synchronization
Write-Host "Connecting to Cloudflare Sync Worker..." -ForegroundColor Gray
$TargetUrl = "$WorkerUrl/get-auth"

$Headers = @{
    "Authorization" = "Bearer $SecretKey"
}

try {
    # Send GET request to pull the auth.json
    $Response = Invoke-WebRequest -Uri $TargetUrl -Headers $Headers -Method Get -UseBasicParsing
    
    # Verify we got a valid JSON
    $AuthData = $Response.Content | ConvertFrom-Json
    if (-not $AuthData.tokens -or -not $AuthData.tokens.access_token) {
        throw "Retrieved payload does not appear to be a valid Codex auth.json."
    }
    
    # Target directory: ~/.codex/
    $CodexDir = Join-Path $env:USERPROFILE ".codex"
    if (-not (Test-Path $CodexDir)) {
        New-Item -ItemType Directory -Path $CodexDir -Force | Out-Null
    }
    
    $AuthFile = Join-Path $CodexDir "auth.json"
    # Write back pretty formatted JSON to ~/.codex/auth.json
    $Response.Content | Out-File -FilePath $AuthFile -Encoding utf8 -Force
    
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "✓ Codex Auth successfully synchronized!" -ForegroundColor Green
    Write-Host "Saved to: $AuthFile" -ForegroundColor Gray
    Write-Host "=============================================" -ForegroundColor Green
} catch {
    Write-Host "=============================================" -ForegroundColor Red
    Write-Host "❌ Synchronization Failed!" -ForegroundColor Red
    Write-Host "Details: $_" -ForegroundColor Red
    Write-Host "=============================================" -ForegroundColor Red
    Exit 1
}
