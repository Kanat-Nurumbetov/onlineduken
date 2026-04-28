param(
    [int]$Workers = 3,
    [switch]$Allure,
    [switch]$SkipHealthcheck,
    [string]$BuildName = "",
    [string]$AllureResultsDir = "allure-results"
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

function Require-Env([string]$Name) {
    if (-not [Environment]::GetEnvironmentVariable($Name, "Process")) {
        throw "Missing required environment variable: $Name"
    }
}

Load-DotEnv $EnvFile | Out-Null
$pythonCommand = Resolve-PythonCommand

$env:TARGET = "browserstack"
$env:PLATFORM = "android"
$env:ONLINEDUKEN_ENTRY_MODE = "full"
$env:B2B_SHARED_AUTH_BOOTSTRAP = "false"
$env:B2B_APP_AUTH_BOOTSTRAP = "false"
$env:BROWSERSTACK_WEBVIEW_ENABLED = "false"
if ($BuildName) {
    $env:BROWSERSTACK_BUILD_NAME = $BuildName
} elseif (-not $env:BROWSERSTACK_BUILD_NAME -or $env:BROWSERSTACK_BUILD_NAME -eq "local-dev") {
    $env:BROWSERSTACK_BUILD_NAME = "browserstack-demo-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
}

Require-Env "BROWSERSTACK_USERNAME"
Require-Env "BROWSERSTACK_ACCESS_KEY"
Require-Env "BROWSERSTACK_APP_ANDROID"

Write-Step "Ensuring Python dependencies"
Invoke-External $pythonCommand.FilePath (Join-Command $pythonCommand @("-m", "pip", "install", "--upgrade", "pip")) -IgnoreExitCode
Invoke-External $pythonCommand.FilePath (Join-Command $pythonCommand @("-m", "pip", "install", "-r", (Join-Path $ProjectRoot "requirements-ci.txt")))
Invoke-External $pythonCommand.FilePath (Join-Command $pythonCommand @("-m", "pip", "install", "-e", $ProjectRoot, "--no-deps"))

if (-not $SkipHealthcheck) {
    Write-Step "Checking test environment availability"
    Invoke-External $pythonCommand.FilePath (Join-Command $pythonCommand @("-m", "mobile_automation.healthcheck"))
}

$pytestArgs = @(
    "-m", "smoke and browserstack_safe and not manual",
    "-n", "$Workers",
    "--maxfail=1",
    "-q"
)
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

Write-Step "Running BrowserStack smoke on $Workers workers"
Invoke-External $pythonCommand.FilePath (Join-Command $pythonCommand (@("-m", "pytest") + $pytestArgs))
