param(
    [switch]$Headless,
    [switch]$Allure,
    [int]$Workers = 0,
    [string]$KExpression = "",
    [switch]$SkipInstall,
    [string]$AllureResultsDir = "allure-results-web"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env"

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Load-DotEnv([string]$Path) {
    $values = @{}
    if (-not (Test-Path $Path)) {
        return $values
    }
    foreach ($line in Get-Content -Path $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
            continue
        }
        $parts = $trimmed.Split("=", 2)
        $key = $parts[0].Trim()
        $value = $parts[1].Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        if (-not [Environment]::GetEnvironmentVariable($key, "Process")) {
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
        $values[$key] = $value
    }
    return $values
}

function Resolve-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            & py -3.12 --version | Out-Null
            return @{
                FilePath = "py"
                PrefixArgs = @("-3.12")
            }
        } catch {
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{
            FilePath = "python"
            PrefixArgs = @()
        }
    }
    throw "Python was not found. Install Python 3.11+ first."
}

function Join-Command([hashtable]$CommandSpec, [string[]]$Suffix = @()) {
    return @($CommandSpec.PrefixArgs) + $Suffix
}

function Invoke-External([string]$FilePath, [string[]]$Arguments = @(), [switch]$IgnoreExitCode) {
    & $FilePath @Arguments
    $exitCode = $LASTEXITCODE
    if (-not $IgnoreExitCode -and $exitCode -ne 0) {
        throw "Command failed with exit code ${exitCode}: $FilePath $($Arguments -join ' ')"
    }
}

Load-DotEnv $EnvFile | Out-Null
$pythonCommand = Resolve-PythonCommand

# The web tier always drives a local browser; mobile/browserstack targets
# from .env must not leak into this run.
$env:TARGET = "local"
$env:WEB_BROWSER = "chrome"
if ($Headless) {
    $env:WEB_HEADLESS = "true"
}

if (-not $SkipInstall) {
    Write-Step "Ensuring Python dependencies"
    Invoke-External $pythonCommand.FilePath (Join-Command $pythonCommand @("-m", "pip", "install", "-e", "$ProjectRoot[ci]", "-q"))
}

$pytestArgs = @("-m", "web", "-q", "-ra")
if ($KExpression) {
    $pytestArgs += @("-k", $KExpression)
}
if ($Workers -gt 0) {
    $pytestArgs += @("-n", "$Workers")
}
if ($Allure) {
    $allurePath = if ([System.IO.Path]::IsPathRooted($AllureResultsDir)) {
        $AllureResultsDir
    } else {
        Join-Path $ProjectRoot $AllureResultsDir
    }
    if ((Test-Path $allurePath) -and ((Resolve-Path $allurePath).Path.StartsWith($ProjectRoot))) {
        Remove-Item -LiteralPath $allurePath -Recurse -Force
    }
    $pytestArgs += @("--alluredir", $AllureResultsDir)
}

Write-Step "Running OnlineDuken web suite"
Invoke-External $pythonCommand.FilePath (Join-Command $pythonCommand (@("-m", "pytest") + $pytestArgs))
