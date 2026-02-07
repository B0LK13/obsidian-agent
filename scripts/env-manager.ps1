<#
.SYNOPSIS
    Environment and Secrets Manager for development workflows.
.DESCRIPTION
    Securely manage API tokens and environment variables.
.EXAMPLE
    .\env-manager.ps1 list
    .\env-manager.ps1 set CLOUDFLARE_API_TOKEN "your-token"
    .\env-manager.ps1 test
#>

param(
    [Parameter(Position=0)]
    [ValidateSet("list", "get", "set", "delete", "test", "export", "import", "rotate", "help")]
    [string]$Action = "help",
    
    [Parameter(Position=1)]
    [string]$Key,
    
    [Parameter(Position=2)]
    [string]$Value,
    
    [switch]$Force
)

$SecretsDir = "$env:USERPROFILE\.secrets"
$SecretsFile = "$SecretsDir\secrets.json"
$EnvFile = "$SecretsDir\env.ps1"

if (-not (Test-Path $SecretsDir)) {
    New-Item -ItemType Directory -Path $SecretsDir -Force | Out-Null
    icacls $SecretsDir /inheritance:r /grant:r "${env:USERNAME}:(OI)(CI)F" 2>$null | Out-Null
}

$Services = @{
    CLOUDFLARE_API_TOKEN = @{
        Description = "Cloudflare API Token"
        TestUrl = "https://api.cloudflare.com/client/v4/user/tokens/verify"
        RotateUrl = "https://dash.cloudflare.com/profile/api-tokens"
    }
    HOSTINGER_API_TOKEN = @{
        Description = "Hostinger API Token"
        TestUrl = "https://developers.hostinger.com/api/vps/v1/virtual-machines"
        RotateUrl = "https://hpanel.hostinger.com/api"
    }
    GITHUB_TOKEN = @{
        Description = "GitHub Personal Access Token"
        TestUrl = "https://api.github.com/user"
        RotateUrl = "https://github.com/settings/tokens"
    }
    BRAVE_API_KEY = @{
        Description = "Brave Search API Key"
        TestUrl = "https://api.search.brave.com/res/v1/web/search?q=test"
        RotateUrl = "https://brave.com/search/api/"
    }
    OPENAI_API_KEY = @{
        Description = "OpenAI API Key"
        TestUrl = "https://api.openai.com/v1/models"
        RotateUrl = "https://platform.openai.com/api-keys"
    }
    DISCORD_TOKEN = @{
        Description = "Discord Bot Token"
        TestUrl = "https://discord.com/api/v10/users/@me"
        RotateUrl = "https://discord.com/developers/applications"
    }
    GOOGLE_API_KEY = @{
        Description = "Google/Gemini API Key"
        TestUrl = "https://generativelanguage.googleapis.com/v1/models"
        RotateUrl = "https://aistudio.google.com/app/apikey"
    }
}

function Show-Help {
    $helpText = @'
========================================================
        Environment and Secrets Manager
========================================================

Usage: .\env-manager.ps1 ACTION [KEY] [VALUE]

Actions:
  list              List all stored secrets (masked)
  get KEY           Get a specific secret value
  set KEY VALUE     Set or update a secret
  delete KEY        Delete a secret
  test [KEY]        Test API token validity
  export            Export secrets to env.ps1 loader
  import FILE       Import secrets from .env file
  rotate [KEY]      Show rotation URL for a service
  help              Show this help message

Supported Services:
  CLOUDFLARE_API_TOKEN    Cloudflare API
  HOSTINGER_API_TOKEN     Hostinger VPS API
  GITHUB_TOKEN            GitHub Personal Access Token
  BRAVE_API_KEY           Brave Search API
  OPENAI_API_KEY          OpenAI API
  DISCORD_TOKEN           Discord Bot Token
  GOOGLE_API_KEY          Google/Gemini API

Examples:
  .\env-manager.ps1 set CLOUDFLARE_API_TOKEN "your-token"
  .\env-manager.ps1 test CLOUDFLARE_API_TOKEN
  .\env-manager.ps1 list
  .\env-manager.ps1 export

========================================================
'@
    Write-Host $helpText -ForegroundColor Cyan
}

function Get-Secrets {
    if (Test-Path $SecretsFile) {
        $content = Get-Content $SecretsFile -Raw
        if ($content) {
            $json = $content | ConvertFrom-Json
            $ht = @{}
            $json.PSObject.Properties | ForEach-Object { $ht[$_.Name] = $_.Value }
            return $ht
        }
    }
    return @{}
}

function Save-Secrets {
    param([hashtable]$Secrets)
    $Secrets | ConvertTo-Json -Depth 5 -Compress | Out-File $SecretsFile -Encoding UTF8
}

function Get-MaskedValue {
    param([string]$Val)
    if ($Val.Length -le 8) { return "****" }
    return $Val.Substring(0, 4) + ("*" * ($Val.Length - 8)) + $Val.Substring($Val.Length - 4)
}

function Invoke-ListSecrets {
    $secrets = Get-Secrets
    
    Write-Host ""
    Write-Host "Stored Secrets:" -ForegroundColor Yellow
    Write-Host "------------------------------------------------" -ForegroundColor Gray
    
    if ($secrets.Count -eq 0) {
        Write-Host "  No secrets stored yet." -ForegroundColor Gray
    } else {
        foreach ($k in $secrets.Keys | Sort-Object) {
            $masked = Get-MaskedValue $secrets[$k]
            $desc = if ($Services.ContainsKey($k)) { $Services[$k].Description } else { "Custom" }
            Write-Host "  $k" -ForegroundColor Green -NoNewline
            Write-Host " = $masked " -ForegroundColor DarkGray -NoNewline
            Write-Host "($desc)" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

function Invoke-GetSecret {
    param([string]$K)
    if (-not $K) { Write-Host "Error: Key required" -ForegroundColor Red; return }
    $secrets = Get-Secrets
    if ($secrets.ContainsKey($K)) {
        Write-Host $secrets[$K]
    } else {
        Write-Host "Secret '$K' not found" -ForegroundColor Yellow
    }
}

function Invoke-SetSecret {
    param([string]$K, [string]$V)
    if (-not $K) { Write-Host "Error: Key required" -ForegroundColor Red; return }
    
    if (-not $V) {
        $secureVal = Read-Host "Enter value for $K" -AsSecureString
        $V = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureVal)
        )
    }
    
    $secrets = Get-Secrets
    $isNew = -not $secrets.ContainsKey($K)
    $secrets[$K] = $V
    Save-Secrets $secrets
    
    [Environment]::SetEnvironmentVariable($K, $V, "Process")
    
    if ($isNew) {
        Write-Host "[OK] Secret '$K' created" -ForegroundColor Green
    } else {
        Write-Host "[OK] Secret '$K' updated" -ForegroundColor Green
    }
    
    if ($Services.ContainsKey($K)) {
        $testNow = Read-Host "Test this token now? (y/n)"
        if ($testNow -eq "y") { Invoke-TestSecret $K }
    }
}

function Invoke-DeleteSecret {
    param([string]$K)
    if (-not $K) { Write-Host "Error: Key required" -ForegroundColor Red; return }
    
    $secrets = Get-Secrets
    if ($secrets.ContainsKey($K)) {
        if (-not $Force) {
            $confirm = Read-Host "Delete secret '$K'? (y/n)"
            if ($confirm -ne "y") { Write-Host "Cancelled" -ForegroundColor Yellow; return }
        }
        $secrets.Remove($K)
        Save-Secrets $secrets
        Write-Host "[OK] Secret '$K' deleted" -ForegroundColor Green
    } else {
        Write-Host "Secret '$K' not found" -ForegroundColor Yellow
    }
}

function Invoke-TestSecret {
    param([string]$K)
    
    $secrets = Get-Secrets
    
    if (-not $K) {
        Write-Host ""
        Write-Host "Testing all stored API tokens..." -ForegroundColor Yellow
        Write-Host ""
        foreach ($sk in $secrets.Keys) {
            if ($Services.ContainsKey($sk)) { Invoke-TestSecret $sk }
        }
        return
    }
    
    if (-not $secrets.ContainsKey($K)) {
        Write-Host "Secret '$K' not found" -ForegroundColor Yellow
        return
    }
    
    if (-not $Services.ContainsKey($K)) {
        Write-Host "No test available for '$K'" -ForegroundColor Gray
        return
    }
    
    $svc = $Services[$K]
    $token = $secrets[$K]
    
    Write-Host -NoNewline "Testing $($svc.Description)... "
    
    try {
        $headers = @{ "Authorization" = "Bearer $token" }
        if ($K -eq "BRAVE_API_KEY") { $headers = @{ "X-Subscription-Token" = $token } }
        if ($K -eq "DISCORD_TOKEN") { $headers = @{ "Authorization" = "Bot $token" } }
        
        $url = $svc.TestUrl
        if ($K -eq "GOOGLE_API_KEY") { $url = "$url`?key=$token"; $headers = @{} }
        
        $null = Invoke-RestMethod -Uri $url -Headers $headers -Method Get -TimeoutSec 10 -ErrorAction Stop
        Write-Host "[VALID]" -ForegroundColor Green
    }
    catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code -eq 401 -or $code -eq 403) {
            Write-Host "[INVALID]" -ForegroundColor Red
            Write-Host "   Rotate at: $($svc.RotateUrl)" -ForegroundColor Yellow
        } else {
            Write-Host "[ERROR: $code]" -ForegroundColor Yellow
        }
    }
}

function Invoke-ExportSecrets {
    $secrets = Get-Secrets
    
    $lines = @()
    $lines += "# Environment Variables Loader"
    $lines += "# Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $lines += "# Source this file: . ~/.secrets/env.ps1"
    $lines += ""
    
    foreach ($k in $secrets.Keys | Sort-Object) {
        $v = $secrets[$k]
        $lines += "`$env:$k = '$v'"
    }
    
    $lines += ""
    $lines += "Write-Host 'Loaded $($secrets.Count) environment variables' -ForegroundColor Green"
    
    $lines | Out-File $EnvFile -Encoding UTF8
    Write-Host "[OK] Exported to $EnvFile" -ForegroundColor Green
    Write-Host "Load with: . ~/.secrets/env.ps1" -ForegroundColor Yellow
}

function Invoke-ImportSecrets {
    param([string]$FilePath)
    if (-not $FilePath) { Write-Host "Error: File path required" -ForegroundColor Red; return }
    if (-not (Test-Path $FilePath)) { Write-Host "Error: File not found" -ForegroundColor Red; return }
    
    $secrets = Get-Secrets
    $imported = 0
    
    Get-Content $FilePath | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            if ($line -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
                $k = $matches[1]
                $v = $matches[2].Trim('"').Trim("'")
                $secrets[$k] = $v
                $imported++
            }
        }
    }
    
    Save-Secrets $secrets
    Write-Host "[OK] Imported $imported secrets from $FilePath" -ForegroundColor Green
}

function Invoke-ShowRotateUrl {
    param([string]$K)
    
    if (-not $K) {
        Write-Host ""
        Write-Host "Token Rotation URLs:" -ForegroundColor Yellow
        Write-Host ""
        foreach ($sk in $Services.Keys | Sort-Object) {
            Write-Host "  $sk" -ForegroundColor Green
            Write-Host "    $($Services[$sk].RotateUrl)" -ForegroundColor Cyan
        }
        Write-Host ""
        return
    }
    
    if ($Services.ContainsKey($K)) {
        Write-Host ""
        Write-Host "Rotate $($Services[$K].Description) at:" -ForegroundColor Yellow
        Write-Host "  $($Services[$K].RotateUrl)" -ForegroundColor Cyan
        Write-Host ""
        $open = Read-Host "Open in browser? (y/n)"
        if ($open -eq "y") { Start-Process $Services[$K].RotateUrl }
    } else {
        Write-Host "Unknown service: $K" -ForegroundColor Yellow
    }
}

switch ($Action) {
    "list"   { Invoke-ListSecrets }
    "get"    { Invoke-GetSecret $Key }
    "set"    { Invoke-SetSecret $Key $Value }
    "delete" { Invoke-DeleteSecret $Key }
    "test"   { Invoke-TestSecret $Key }
    "export" { Invoke-ExportSecrets }
    "import" { Invoke-ImportSecrets $Key }
    "rotate" { Invoke-ShowRotateUrl $Key }
    "help"   { Show-Help }
    default  { Show-Help }
}
