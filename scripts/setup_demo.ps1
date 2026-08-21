[CmdletBinding()]
param(
    [string]$PythonBin = $env:PYTHON_BIN,
    [string]$VenvPath = $env:ADM_DEMO_VENV,
    [string]$PipConfigFile = $env:ADM_PIP_CONFIG_FILE
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

function Resolve-PipConfigFile {
    param(
        [string]$RequestedPath,
        [string]$ProjectRoot
    )

    if (-not [string]::IsNullOrWhiteSpace($RequestedPath)) {
        if (-not (Test-Path $RequestedPath)) {
            throw "Le fichier pip.ini indiqué ('$RequestedPath') est introuvable."
        }
        return (Resolve-Path $RequestedPath).Path
    }

    $defaultPath = Join-Path $ProjectRoot "pip.ini"
    if (Test-Path $defaultPath) {
        return (Resolve-Path $defaultPath).Path
    }

    return $null
}

function Resolve-PythonCommand {
    param([string]$RequestedCommand)

    if (-not [string]::IsNullOrWhiteSpace($RequestedCommand)) {
        if ($null -eq (Get-Command $RequestedCommand -ErrorAction SilentlyContinue)) {
            throw "L'interpréteur Python '$RequestedCommand' est introuvable. Vérifiez -PythonBin ou PYTHON_BIN."
        }
        return $RequestedCommand
    }

    foreach ($candidate in @("py", "python", "python3")) {
        if ($null -ne (Get-Command $candidate -ErrorAction SilentlyContinue)) {
            return $candidate
        }
    }

    throw "Aucun interpréteur Python n'a été trouvé. Installez Python 3.11 ou indiquez son chemin avec -PythonBin."
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
    $PythonBin = Resolve-PythonCommand -RequestedCommand $PythonBin
    
    $resolvedPipConfigFile = Resolve-PipConfigFile -RequestedPath $PipConfigFile -ProjectRoot $ProjectRoot
    if ($null -ne $resolvedPipConfigFile) {
        $env:PIP_CONFIG_FILE = $resolvedPipConfigFile
        Write-Host "Dépôt pip personnalisé détecté : utilisation de '$resolvedPipConfigFile'."
    } else {
        Write-Host "Aucun pip.ini trouvé : utilisation du dépôt PyPI par défaut."
    }

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
