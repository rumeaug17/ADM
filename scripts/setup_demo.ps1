[CmdletBinding()]
param(
    [string]$PythonBin = "py",
    [string]$VenvPath = $env:ADM_DEMO_VENV
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($VenvPath)) {
    $VenvPath = Join-Path $ProjectRoot ".venv"
}
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$ConfigFile = Join-Path $ProjectRoot ".adm-demo.json"

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$CommandArguments
    )

    & $Command @CommandArguments
    if ($LASTEXITCODE -ne 0) {
        throw "La commande '$Command' a échoué avec le code $LASTEXITCODE."
    }
}

function New-RandomToken {
    param([int]$ByteCount)

    $bytes = New-Object byte[] $ByteCount
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
    }
    finally {
        $generator.Dispose()
    }
    return [Convert]::ToBase64String($bytes).TrimEnd("=").Replace("+", "-").Replace("/", "_")
}

Push-Location $ProjectRoot
try {
    Write-Host "Création de l'environnement Python de démonstration..."
    Invoke-CheckedCommand -Command $PythonBin -CommandArguments @("-m", "venv", $VenvPath)
    Invoke-CheckedCommand -Command $VenvPython -CommandArguments @(
        "-m", "pip", "install", "--upgrade", "pip"
    )
    Invoke-CheckedCommand -Command $VenvPython -CommandArguments @(
        "-m", "pip", "install", "-e", ".[dev]"
    )

    Write-Host "Construction de l'artefact..."
    Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
    Invoke-CheckedCommand -Command $VenvPython -CommandArguments @("-m", "build")

    Write-Host "Exécution des contrôles qualité..."
    Invoke-CheckedCommand -Command $VenvPython -CommandArguments @("-m", "ruff", "check", ".")
    Invoke-CheckedCommand -Command $VenvPython -CommandArguments @(
        "-m", "ruff", "format", "--check", "."
    )
    Invoke-CheckedCommand -Command $VenvPython -CommandArguments @(
        "-m", "mypy", "src", "main.py"
    )
    Invoke-CheckedCommand -Command $VenvPython -CommandArguments @("-m", "pytest")

    Write-Host "Génération des données fictives..."
    Invoke-CheckedCommand -Command $VenvPython -CommandArguments @(
        "scripts/generate_data_json.py"
    )

    Write-Host "Configuration du mode démo standalone..."
    $configuration = [ordered]@{
        ADM_DB_BACKEND  = "json"
        ADM_DATABASE_URL = Join-Path $ProjectRoot "applications.json"
        ADM_SECRET_KEY  = New-RandomToken 48
        ADM_USERNAME    = "demo-$(New-RandomToken 6)"
        ADM_PASSWORD    = New-RandomToken 18
    }
    $configuration | ConvertTo-Json | Set-Content -Encoding UTF8 $ConfigFile

    $version = & git describe --tags --abbrev=0 2>$null
    if ($LASTEXITCODE -ne 0) {
        $version = "v0.1.0"
    }
    Set-Content -Encoding UTF8 (Join-Path $ProjectRoot "static\version.txt") $version

    Write-Host "Installation terminée. Lancez la démo avec : .\scripts\run_demo.ps1"
}
finally {
    Pop-Location
}
