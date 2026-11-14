
param(
    [string]$KitDirectory = $PSScriptRoot,
    [ValidateSet('Default', 'SlowVm')]
    [string]$Profile = 'Default',
    [ValidateRange(1, 1800)]
    [int]$InstallTimeoutSeconds,
    [ValidateRange(1, 300)]
    [int]$GuiTimeoutSeconds,
    [ValidateRange(1, 180)]
    [int]$ExitTimeoutSeconds,
    [string]$DiagnosticLog
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'TauriAcceptanceSupport.ps1')
$waits = Get-AcceptanceWaits $Profile $PSBoundParameters
$acceptanceLog = Get-AcceptanceLogPath $DiagnosticLog

function Get-WebView2Version {
    $client = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
    $keys = @(
        "HKLM:\Software\WOW6432Node\Microsoft\EdgeUpdate\Clients\$client"
        "HKLM:\Software\Microsoft\EdgeUpdate\Clients\$client"
        "HKCU:\Software\Microsoft\EdgeUpdate\Clients\$client"
    )
    $versions = @(Get-ItemProperty -LiteralPath $keys -Name pv -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty pv |
        Where-Object { $_ -match '^\d+(\.\d+){3}$' -and $_ -ne '0.0.0.0' } | Sort-Object -Unique)
    if ($versions.Count) { $versions -join ',' } else { 'absent' }
}

Write-Host "Diagnostic log: $acceptanceLog"
Write-AcceptanceEvent 'INFO' 'configuration' $null 0 "profile=$Profile installSeconds=$($waits.InstallTimeoutSeconds) guiSeconds=$($waits.GuiTimeoutSeconds) exitSeconds=$($waits.ExitTimeoutSeconds)"
$timer = [Diagnostics.Stopwatch]::StartNew()
$phase = 'package-integrity'
$exitCode = 0
try {
    $kit = (Resolve-Path -LiteralPath $KitDirectory).Path
    $manifest = Get-Content -Raw -LiteralPath (Join-Path $kit 'build.json') | ConvertFrom-Json
    $installer = Join-Path $kit 'Rigarus-Dispatch-x64-setup.exe'
    $smoke = (Resolve-Path -LiteralPath (Join-Path $kit 'Test-TauriDesktop.ps1')).Path
    $hash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash
    if ($manifest.commit -notmatch '^[a-f0-9]{40}$' -or $hash -ne $manifest.installerSha256) {
        Stop-Acceptance 'FAIL' $phase $timer 0 'invalidCommitOrSha256=true'
    }
    Write-AcceptanceEvent 'PASS' $phase $timer 0 "commit=$($manifest.commit) sha256=$hash"

    $phase = 'environment'
    $timer.Restart()
    $os = Get-CimInstance -ClassName Win32_OperatingSystem -OperationTimeoutSec 15
    if ([int]$os.BuildNumber -lt 22000 -or $os.ProductType -ne 1 -or
        [Environment]::GetEnvironmentVariable('PROCESSOR_ARCHITECTURE', 'Machine') -ne 'AMD64') {
        Stop-Acceptance 'BLOCKED' $phase $timer 0 'expected=Windows11-x64-client'
    }
    if ([Net.NetworkInformation.NetworkInterface]::GetIsNetworkAvailable()) {
        Stop-Acceptance 'BLOCKED' $phase $timer 0 'activeNetworkAdapter=true'
    }

    # Windows app execution aliases alone do not indicate a Python installation.
    $toolCommands = @('node.exe', 'cargo.exe', 'rustc.exe', 'cl.exe', 'python.exe', 'py.exe', 'uv.exe')
    $tools = @(Get-Command -Name $toolCommands -CommandType Application -All -ErrorAction SilentlyContinue |
        Where-Object Source -NotLike "$env:LOCALAPPDATA\Microsoft\WindowsApps\*")
    if ($tools.Count) { Stop-Acceptance 'BLOCKED' $phase $timer 0 'developerCommandsPresent=true' }

    $installedApps = @(
        Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
            'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
            'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue
    )
    if ($installedApps.DisplayName -like 'Rigarus Dispatch*') {
        Stop-Acceptance 'BLOCKED' $phase $timer 0 'existingRigarusInstall=true'
    }
    if ($installedApps.DisplayName -match '^(Node\.js|Python [0-9]|Rust|Microsoft Visual Studio|Visual Studio (Community|Professional|Enterprise|Build Tools))') {
        Stop-Acceptance 'BLOCKED' $phase $timer 0 'developerAppsPresent=true'
    }
    $dotnet = Get-Command dotnet.exe -CommandType Application -ErrorAction SilentlyContinue
    if ($dotnet) {
        $sdkList = New-TemporaryFile
        $sdkProbe = $null
        try {
            $sdkProbe = Start-Process -FilePath $dotnet.Source -ArgumentList '--list-sdks' -WindowStyle Hidden -PassThru -RedirectStandardOutput $sdkList.FullName
            if (-not $sdkProbe.WaitForExit(15000) -or $sdkProbe.ExitCode -ne 0) {
                Stop-Acceptance 'BLOCKED' $phase $timer 15 'dotnetSdkProbeUnavailable=true'
            }
            if (Get-Content -LiteralPath $sdkList.FullName | Where-Object { $_.Trim() }) {
                Stop-Acceptance 'BLOCKED' $phase $timer 0 'dotnetSdkPresent=true'
            }
        }
        finally {
            Stop-AcceptanceProcess $sdkProbe 'sdk-probe-cleanup' $waits.ExitTimeoutSeconds
            Remove-Item -LiteralPath $sdkList.FullName -Force -ErrorAction SilentlyContinue
        }
    }
    $before = Get-WebView2Version
    Write-AcceptanceEvent 'PASS' $phase $timer 0 "windowsBuild=$($os.BuildNumber) offline=yes developerTools=absent webView2Before=$before"

    $phase = 'install'
    $destination = Join-Path $env:LOCALAPPDATA ('Rigarus Offline Test ' + [Guid]::NewGuid().ToString('N'))
    $timer.Restart()
    Write-AcceptanceEvent 'START' $phase $timer $waits.InstallTimeoutSeconds 'process=not-started'
    # NSIS requires /D to be last and unquoted, even for paths containing spaces.
    $setup = Start-Process -FilePath $installer -ArgumentList "/S /D=$destination" -WindowStyle Hidden -PassThru
    try {
        Wait-AcceptanceProcess $setup $phase $waits.InstallTimeoutSeconds $timer
    }
    finally { $setup.Dispose() }

    $phase = 'runtime-verification'
    $timer.Restart()
    $after = Get-WebView2Version
    if ($after -eq 'absent') { Stop-Acceptance 'FAIL' $phase $timer 0 'webView2After=absent' }
    Write-AcceptanceEvent 'PASS' $phase $timer 0 "webView2After=$after"

    $phase = 'desktop-smoke'
    $exe = Join-Path $destination 'rigarus-dispatch.exe'
    # Supervises the entire child, including a stuck synchronous UI Automation call.
    $workerLimit = [Math]::Min(2700, 60 * $waits.GuiTimeoutSeconds + 8 * $waits.ExitTimeoutSeconds)
    $arguments = @('-NoProfile', '-ExecutionPolicy Bypass', '-STA', '-File', ('"{0}"' -f $smoke),
        '-Executable', ('"{0}"' -f $exe), '-RequireOffline', '-IncludeProjects',
        '-Profile', $Profile, '-GuiTimeoutSeconds', $waits.GuiTimeoutSeconds, '-ExitTimeoutSeconds', $waits.ExitTimeoutSeconds,
        '-DiagnosticLog', ('"{0}"' -f $acceptanceLog))
    $timer.Restart()
    Write-AcceptanceEvent 'START' $phase $timer $workerLimit 'process=not-started'
    $workerStart = [Diagnostics.ProcessStartInfo]::new((Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'), ($arguments -join ' '))
    $workerStart.UseShellExecute = $false
    $worker = [Diagnostics.Process]::Start($workerStart)
    try {
        if (-not $worker.WaitForExit($workerLimit * 1000)) {
            Stop-Acceptance 'TIMEOUT' $phase $timer $workerLimit (Get-AcceptanceProcessState $worker)
        }
        switch ($worker.ExitCode) {
            0 { Write-AcceptanceEvent 'PASS' $phase $timer $workerLimit (Get-AcceptanceProcessState $worker) }
            2 { Stop-Acceptance 'TIMEOUT' $phase $timer $workerLimit (Get-AcceptanceProcessState $worker) }
            3 { Stop-Acceptance 'BLOCKED' $phase $timer $workerLimit (Get-AcceptanceProcessState $worker) }
            default { Stop-Acceptance 'FAIL' $phase $timer $workerLimit (Get-AcceptanceProcessState $worker) }
        }
    }
    finally { Stop-AcceptanceProcess $worker 'worker-cleanup' $waits.ExitTimeoutSeconds }
    if ([Net.NetworkInformation.NetworkInterface]::GetIsNetworkAvailable()) {
        Stop-Acceptance 'BLOCKED' 'environment' $timer 0 'activeNetworkAdapterAfterSmoke=true'
    }
    Write-AcceptanceEvent 'PASS' 'offline-acceptance' $null 0 'network=offline'
}
catch {
    $unexpected = if ($phase -eq 'environment') { 'BLOCKED' } else { 'FAIL' }
    $exitCode = Get-AcceptanceExitCode $_ $phase $timer $unexpected
}
exit $exitCode
