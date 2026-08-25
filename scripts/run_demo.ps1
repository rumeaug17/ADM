[CmdletBinding()]
param(
    [string]$VenvPath = $env:ADM_DEMO_VENV,
    [ValidateSet("on", "off")]
    [string]$DebugMode = "off"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($VenvPath)) {
    $VenvPath = Join-Path $ProjectRoot ".venv"
}
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$ConfigFile = Join-Path $ProjectRoot ".adm-demo.json"

if (-not (Test-Path $ConfigFile) -or -not (Test-Path $VenvPython)) {
    throw "La démo n'est pas configurée. Exécutez d'abord .\scripts\setup_demo.ps1."
}

$configuration = Get-Content -Raw $ConfigFile | ConvertFrom-Json
$requiredVariables = @(
    "ADM_DB_BACKEND",
    "ADM_DATABASE_URL",
    "ADM_SECRET_KEY",
    "ADM_ACCOUNTS_URL"
)
foreach ($variableName in $requiredVariables) {
    $value = $configuration.$variableName
    if (-not ($value -is [string]) -or [string]::IsNullOrWhiteSpace($value)) {
        throw "La variable $variableName est absente de la configuration de démonstration."
    }
    [Environment]::SetEnvironmentVariable($variableName, $value, "Process")
}

if ($configuration.DemoUsername -and $configuration.DemoPassword) {
    Write-Host "Identifiants de démonstration : $($configuration.DemoUsername) / $($configuration.DemoPassword)"
} else {
    Write-Host "Aucun compte de démonstration trouvé : créez-en un avec scripts\create_account.py."
}

Push-Location $ProjectRoot
try {
    $MainArguments = @("main.py")
    if ($DebugMode -eq "on") {
        $MainArguments += "--debug"
    }
    & $VenvPython @MainArguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
