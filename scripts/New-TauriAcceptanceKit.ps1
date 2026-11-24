param(
    [Parameter(Mandatory = $true)]
    [string]$Installer,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-f0-9]{40}$')]
    [string]$Commit,
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$installerPath = (Resolve-Path -LiteralPath $Installer).Path
$output = New-Item -ItemType Directory -Path $OutputDirectory
$copy = Join-Path $output.FullName 'Rigarus-Dispatch-x64-setup.exe'
Copy-Item -LiteralPath $installerPath -Destination $copy
foreach ($script in @('Test-TauriOfflineInstall.ps1', 'Test-TauriDesktop.ps1', 'TauriAcceptanceSupport.ps1', 'TauriUiaDiagnostics.ps1', 'TauriSqliteSnapshot.ps1')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $script) -Destination $output.FullName
}
[ordered]@{
    commit = $Commit
    installerSha256 = (Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output.FullName 'build.json') -Encoding ascii
