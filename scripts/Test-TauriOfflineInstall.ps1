param(
    [string]$KitDirectory = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'
$kit = (Resolve-Path -LiteralPath $KitDirectory).Path
$manifest = Get-Content -Raw -LiteralPath (Join-Path $kit 'build.json') | ConvertFrom-Json
$installer = Join-Path $kit 'Rigarus-Dispatch-x64-setup.exe'
$smoke = Join-Path $kit 'Test-TauriDesktop.ps1'
$hash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash
if ($manifest.commit -notmatch '^[a-f0-9]{40}$' -or $hash -ne $manifest.installerSha256) {
    throw 'The acceptance kit has invalid build metadata or an installer hash mismatch.'
}

$os = Get-CimInstance -ClassName Win32_OperatingSystem
if ([int]$os.BuildNumber -lt 22000 -or $os.ProductType -ne 1 -or
    [Environment]::GetEnvironmentVariable('PROCESSOR_ARCHITECTURE', 'Machine') -ne 'AMD64') {
    throw 'Use a Windows 11 x64 client test environment.'
}
if ([Net.NetworkInformation.NetworkInterface]::GetIsNetworkAvailable()) {
    throw 'Disconnect all network adapters in the test environment before installing.'
}

# Windows app execution aliases alone do not indicate a Python installation.
$toolCommands = @('node.exe', 'cargo.exe', 'rustc.exe', 'cl.exe', 'python.exe', 'py.exe')
$tools = @(Get-Command -Name $toolCommands -CommandType Application -All -ErrorAction SilentlyContinue |
    Where-Object Source -NotLike "$env:LOCALAPPDATA\Microsoft\WindowsApps\*" |
    Select-Object -ExpandProperty Name -Unique)
if ($tools.Count) {
    throw "Use a clean test environment. Developer commands found on PATH: $($tools -join ', ')."
}

$installedApps = @(
    Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue
)
if ($installedApps.DisplayName -like 'Rigarus Dispatch*') {
    throw 'Use a fresh test environment without an existing Rigarus Dispatch installation.'
}
$developerApps = @($installedApps.DisplayName | Where-Object {
    $_ -match '^(Node\.js|Python [0-9]|Rust|Microsoft Visual Studio|Visual Studio (Community|Professional|Enterprise|Build Tools))'
})
if ($developerApps.Count) {
    throw "Use a clean test environment. Developer tooling found in installed apps: $($developerApps -join ', ')."
}

function Get-WebView2Version {
    $client = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
    $keys = @(
        "HKLM:\Software\WOW6432Node\Microsoft\EdgeUpdate\Clients\$client"
        "HKLM:\Software\Microsoft\EdgeUpdate\Clients\$client"
        "HKCU:\Software\Microsoft\EdgeUpdate\Clients\$client"
    )
    $versions = @(Get-ItemProperty -LiteralPath $keys -Name pv -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty pv | Where-Object { $_ -and $_ -ne '0.0.0.0' } | Sort-Object -Unique)
    if ($versions.Count) { $versions -join ', ' } else { 'absent' }
}

Write-Output "Commit: $($manifest.commit)"
Write-Output "Installer SHA-256: $hash"
Write-Output "Windows: $($os.Caption) $($os.Version) x64"
Write-Output 'Network: no active adapter before install'
Write-Output 'Developer tools: none found on PATH or in installed apps'
Write-Output "WebView2 before install: $(Get-WebView2Version)"

$destination = Join-Path $env:LOCALAPPDATA ('Rigarus Offline Test ' + [Guid]::NewGuid().ToString('N'))
# NSIS requires /D to be last and unquoted, even for paths containing spaces.
$setup = Start-Process -FilePath $installer -ArgumentList "/S /D=$destination" -WindowStyle Hidden -PassThru
try {
    if (-not $setup.WaitForExit(300000)) {
        throw 'Installation timed out after five minutes.'
    }
    if ($setup.ExitCode -ne 0) { throw "Installation failed with exit code $($setup.ExitCode)." }
}
finally {
    $setup.Dispose()
}
Write-Output "WebView2 after install: $(Get-WebView2Version)"

$exe = Join-Path $destination 'rigarus-dispatch.exe'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File $smoke -Executable $exe -RequireOffline -IncludeProjects
if ($LASTEXITCODE -ne 0) { throw "Installed desktop smoke test failed with exit code $LASTEXITCODE." }
if ([Net.NetworkInformation.NetworkInterface]::GetIsNetworkAvailable()) {
    throw 'An active network adapter was detected after the smoke test.'
}
Write-Output 'PASS: Offline Windows installation and installed desktop smoke test.'
