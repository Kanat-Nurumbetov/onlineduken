param(
    [int]$Workers = 2,
    [switch]$SafeSmoke,
    [switch]$BootstrapOnly,
    [switch]$Allure,
    [string]$EntryMode = "token",
    [string]$BaseAvdName = "Medium_Phone_API_36.0",
    [string]$ParallelAvdName = "Medium_Phone_Parallel",
    [string]$AllureResultsDir = "allure-results"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env"
$ArtifactsDir = Join-Path $ProjectRoot "artifacts"
New-Item -ItemType Directory -Force -Path $ArtifactsDir | Out-Null

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
        $values[$key] = $value
    }
    return $values
}

function Get-ConfigValue([hashtable]$DotEnv, [string]$Name, [string]$Default = "") {
    $fromProcess = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ($fromProcess) {
        return $fromProcess
    }
    if ($DotEnv.ContainsKey($Name) -and $DotEnv[$Name]) {
        return $DotEnv[$Name]
    }
    return $Default
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
    throw "Python was not found. Install Python 3.12+ first."
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

function Invoke-ExternalCapture([string]$FilePath, [string[]]$Arguments = @(), [switch]$IgnoreExitCode) {
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FilePath
    $escapedArguments = foreach ($argument in $Arguments) {
        if ($null -eq $argument) {
            '""'
            continue
        }
        if ($argument -match '[\s"]') {
            '"' + ($argument -replace '(\\*)"', '$1$1\"') + '"'
        } else {
            $argument
        }
    }
    $psi.Arguments = ($escapedArguments -join " ")
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $psi
    [void]$process.Start()
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    if (-not $IgnoreExitCode -and $process.ExitCode -ne 0) {
        $combined = (($stdout, $stderr) | Where-Object { $_ }) -join [Environment]::NewLine
        throw "Command failed with exit code $($process.ExitCode): $FilePath $($Arguments -join ' ')`n$combined"
    }

    return @{
        ExitCode = $process.ExitCode
        StdOut = $stdout
        StdErr = $stderr
    }
}

function Ensure-PythonDependencies([hashtable]$PythonCommand) {
    Write-Step "Ensuring Python dependencies"
    Invoke-External $PythonCommand.FilePath (Join-Command $PythonCommand @("-m", "pip", "install", "--upgrade", "pip")) -IgnoreExitCode
    Invoke-External $PythonCommand.FilePath (Join-Command $PythonCommand @("-m", "pip", "install", "-e", $ProjectRoot))
}

function Resolve-AppiumCli {
    $appiumCmd = Get-Command appium.cmd -ErrorAction SilentlyContinue
    if ($appiumCmd) {
        return $appiumCmd.Source
    }
    $appiumAny = Get-Command appium -ErrorAction SilentlyContinue
    if ($appiumAny) {
        return $appiumAny.Source
    }
    return ""
}

function Ensure-NodeAndAppium([string]$NodePath, [string]$AppiumMainJs) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "npm was not found. Install Node.js first."
    }

    $appiumCli = Resolve-AppiumCli
    if (-not $appiumCli) {
        Write-Step "Installing Appium globally"
        Invoke-External "npm" @("install", "-g", "appium")
        $appiumCli = Resolve-AppiumCli
    }

    if (-not (Test-Path $NodePath)) {
        throw "Configured Node.js path was not found: $NodePath"
    }

    if (-not (Test-Path $AppiumMainJs)) {
        Write-Step "Repairing Appium installation path"
        Invoke-External "npm" @("install", "-g", "appium")
        if (-not (Test-Path $AppiumMainJs)) {
            throw "Appium main script was not found after installation: $AppiumMainJs"
        }
    }

    $driverListResult = Invoke-ExternalCapture "cmd.exe" @("/c", $appiumCli, "driver", "list", "--installed") -IgnoreExitCode
    $installedDrivers = "$($driverListResult.StdOut)`n$($driverListResult.StdErr)"
    if ($driverListResult.ExitCode -ne 0 -or $installedDrivers -notmatch "uiautomator2") {
        Write-Step "Installing Appium UiAutomator2 driver"
        Invoke-ExternalCapture "cmd.exe" @("/c", $appiumCli, "driver", "install", "uiautomator2") | Out-Null
    }
}

function Get-AndroidTools([hashtable]$DotEnv) {
    $sdkRoot = Get-ConfigValue $DotEnv "ANDROID_SDK_ROOT" "C:\Users\Kanat\AppData\Local\Android\Sdk"
    $adbPath = Join-Path $sdkRoot "platform-tools\adb.exe"
    $emulatorPath = Join-Path $sdkRoot "emulator\emulator.exe"
    if (-not (Test-Path $adbPath)) {
        throw "adb.exe was not found: $adbPath"
    }
    if (-not (Test-Path $emulatorPath)) {
        throw "emulator.exe was not found: $emulatorPath"
    }
    return @{
        SdkRoot = $sdkRoot
        AdbPath = $adbPath
        EmulatorPath = $emulatorPath
    }
}

function Get-AvdIniPath([string]$AvdName) {
    return Join-Path $HOME ".android\avd\$AvdName.ini"
}

function Get-AvdDirectory([string]$AvdName) {
    $iniPath = Get-AvdIniPath $AvdName
    if (-not (Test-Path $iniPath)) {
        return ""
    }
    $pathLine = Get-Content $iniPath | Where-Object { $_ -like "path=*" } | Select-Object -First 1
    if (-not $pathLine) {
        return ""
    }
    return $pathLine.Substring(5)
}

function Ensure-ParallelAvd([string]$BaseAvdName, [string]$ParallelAvdName) {
    $parallelIni = Get-AvdIniPath $ParallelAvdName
    $parallelDir = Join-Path $HOME ".android\avd\$ParallelAvdName.avd"
    if ((Test-Path $parallelIni) -and (Test-Path $parallelDir)) {
        return
    }

    $baseIni = Get-AvdIniPath $BaseAvdName
    $baseDir = Get-AvdDirectory $BaseAvdName
    if (-not (Test-Path $baseIni) -or -not (Test-Path $baseDir)) {
        throw "Base AVD '$BaseAvdName' was not found. Create it once in Android Studio first."
    }

    Write-Step "Creating parallel AVD clone '$ParallelAvdName'"
    New-Item -ItemType Directory -Force -Path $parallelDir | Out-Null
    $null = robocopy $baseDir $parallelDir /E /NFL /NDL /NJH /NJS /NC /NS /XF *.lock
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed while creating the parallel AVD clone."
    }

    $configPath = Join-Path $parallelDir "config.ini"
    (Get-Content $configPath) `
        -replace '^AvdId=.*$', "AvdId=$ParallelAvdName" `
        -replace '^avd\.ini\.displayname=.*$', "avd.ini.displayname=Medium Phone Parallel" |
        Set-Content $configPath

    @(
        "avd.ini.encoding=UTF-8",
        "path=$parallelDir",
        "path.rel=avd\$ParallelAvdName.avd",
        "target=android-36"
    ) | Set-Content $parallelIni
}

function Wait-ForDevice([string]$AdbPath, [string]$Serial, [int]$TimeoutSec = 240) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $devices = & $AdbPath devices
        if ($devices -match [regex]::Escape($Serial) + "\s+device") {
            try {
                $boot = (& $AdbPath -s $Serial shell getprop sys.boot_completed 2>$null).Trim()
                if ($boot -eq "1") {
                    return
                }
            } catch {
            }
        }
        Start-Sleep -Seconds 5
    }
    throw "Android device '$Serial' was not ready within ${TimeoutSec}s."
}

function Ensure-Emulator([string]$AdbPath, [string]$EmulatorPath, [string]$Serial, [string]$AvdName, [int]$Port) {
    Invoke-External $AdbPath @("start-server") -IgnoreExitCode
    $devices = & $AdbPath devices
    if ($devices -match [regex]::Escape($Serial) + "\s+device") {
        Wait-ForDevice $AdbPath $Serial
        return
    }

    Write-Step "Starting emulator '$AvdName' on port $Port"
    Start-Process -FilePath $EmulatorPath -ArgumentList @("-avd", $AvdName, "-port", "$Port", "-no-snapshot-load")
    Wait-ForDevice $AdbPath $Serial
}

function Test-HttpReady([string]$Url) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3
        return ($response.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function Stop-ProcessesOnPort([int]$Port) {
    $connections = @(Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($processId in $connections) {
        if (-not $processId -or $processId -eq $PID) {
            continue
        }
        try {
            Stop-Process -Id $processId -Force -ErrorAction Stop
        } catch {
        }
    }
}

function Ensure-AppiumServer([string]$NodePath, [string]$AppiumMainJs, [string]$ServerUrl) {
    $statusUrl = "$($ServerUrl.TrimEnd('/'))/status"
    $uri = [Uri]$ServerUrl
    $port = if ($uri.Port -gt 0) { $uri.Port } else { 4723 }
    $serverHost = if ($uri.Host) { $uri.Host } else { "127.0.0.1" }
    $basePath = if ([string]::IsNullOrWhiteSpace($uri.AbsolutePath)) { "/" } else { $uri.AbsolutePath }
    $stdoutLogPath = Join-Path $ArtifactsDir "appium_bootstrap_${port}_stdout.log"
    $stderrLogPath = Join-Path $ArtifactsDir "appium_bootstrap_${port}_stderr.log"

    Stop-ProcessesOnPort $port
    Start-Sleep -Seconds 2

    Write-Step "Starting Appium on $ServerUrl"
    Start-Process -FilePath $NodePath `
        -ArgumentList @($AppiumMainJs, "server", "--address", $serverHost, "--port", "$port", "--base-path", $basePath, "--log-level", "debug") `
        -RedirectStandardOutput $stdoutLogPath `
        -RedirectStandardError $stderrLogPath

    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        if (Test-HttpReady $statusUrl) {
            return
        }
        Start-Sleep -Seconds 2
    }
    throw "Appium server did not become ready on $ServerUrl. Check logs: $stdoutLogPath and $stderrLogPath"
}

$dotEnv = Load-DotEnv $EnvFile
$pythonCommand = Resolve-PythonCommand
$nodePath = Get-ConfigValue $dotEnv "APPIUM_NODE_PATH" "C:\Program Files\nodejs\node.exe"
$appiumMainJs = Get-ConfigValue $dotEnv "APPIUM_MAIN_JS" "C:\Users\Kanat\AppData\Roaming\npm\node_modules\appium\index.js"
$tools = Get-AndroidTools $dotEnv

Ensure-PythonDependencies $pythonCommand
Ensure-NodeAndAppium $nodePath $appiumMainJs

if ($Workers -ge 2) {
    Ensure-ParallelAvd $BaseAvdName $ParallelAvdName
}

Ensure-Emulator $tools.AdbPath $tools.EmulatorPath "emulator-5554" $BaseAvdName 5554
Ensure-AppiumServer $nodePath $appiumMainJs "http://127.0.0.1:4723"

if ($Workers -ge 2) {
    Ensure-Emulator $tools.AdbPath $tools.EmulatorPath "emulator-5556" $ParallelAvdName 5556
    Ensure-AppiumServer $nodePath $appiumMainJs "http://127.0.0.1:4725"
    $env:LOCAL_ANDROID_DEVICE_MATRIX = "emulator-5554|http://127.0.0.1:4723;emulator-5556|http://127.0.0.1:4725"
} else {
    $env:LOCAL_ANDROID_DEVICE_MATRIX = "emulator-5554|http://127.0.0.1:4723"
}

$env:TARGET = "local"
$env:PLATFORM = "android"
$env:ONLINEDUKEN_ENTRY_MODE = $EntryMode

if ($BootstrapOnly) {
    Write-Step "Bootstrap completed. Tests were not started."
    Write-Host "LOCAL_ANDROID_DEVICE_MATRIX=$env:LOCAL_ANDROID_DEVICE_MATRIX"
    exit 0
}

$pytestArgs = @("-m", "smoke", "-q")
if ($Workers -gt 1) {
    $pytestArgs += @("-n", "$Workers")
}
if ($Allure) {
    $pytestArgs += @("--alluredir", $AllureResultsDir)
}
if ($SafeSmoke) {
    $pytestArgs += @("tests\smoke\test_smoke_suite.py", "-k", "onlineduken_entry or catalog_has_suppliers or orders_navigation or bonuses_navigation_and_history")
}

Write-Step "Running pytest $($pytestArgs -join ' ')"
Invoke-External $pythonCommand.FilePath (Join-Command $pythonCommand (@("-m", "pytest") + $pytestArgs))
