
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'TauriAcceptanceSupport.ps1')
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('rigarus-harness-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testRoot | Out-Null
$acceptanceLog = Get-AcceptanceLogPath (Join-Path $testRoot 'synthetic.log')

function Assert-Result([scriptblock]$Action, [int]$ExpectedCode, [string]$ExpectedEvent) {
    $actualCode = 0
    try { & $Action }
    catch { $actualCode = Get-AcceptanceExitCode $_ 'harness-test' $null }
    $lastEvent = Get-Content -LiteralPath $acceptanceLog -Tail 1
    if ($actualCode -ne $ExpectedCode -or $lastEvent -notmatch $ExpectedEvent) {
        throw "Expected exit $ExpectedCode and event $ExpectedEvent. Received exit $actualCode and $lastEvent"
    }
    Write-Host "Verified exit $ExpectedCode and event $ExpectedEvent"
}

function Test-InstallerProcess([string]$Command, [int]$Seconds, [int]$Code, [string]$Event) {
    $installer = Start-Process -FilePath powershell.exe -ArgumentList @('-NoProfile', '-Command', $Command) -WindowStyle Hidden -PassThru
    try {
        Assert-Result {
            Wait-AcceptanceProcess $installer 'install' $Seconds ([Diagnostics.Stopwatch]::StartNew())
        } $Code $Event
    }
    finally { Stop-AcceptanceProcess $installer 'test-cleanup' 5 }
}

try {
    $defaults = Get-AcceptanceWaits 'Default' @{}
    $slow = Get-AcceptanceWaits 'SlowVm' @{ GuiTimeoutSeconds = 120 }
    if ($defaults.InstallTimeoutSeconds -ne 300 -or $defaults.GuiTimeoutSeconds -ne 30 -or
        $defaults.ExitTimeoutSeconds -ne 12 -or $slow.InstallTimeoutSeconds -ne 900 -or
        $slow.GuiTimeoutSeconds -ne 120 -or $slow.ExitTimeoutSeconds -ne 60) {
        throw 'Unexpected defaults, SlowVm profile, or override precedence.'
    }
    Test-InstallerProcess 'exit 0' 15 0 '^status=PASS phase=install elapsedMs=\d+ limitSeconds=15 state=pid=\d+ process=exited exitCode=0$'
    Test-InstallerProcess 'Start-Sleep -Seconds 2; exit 0' 15 0 '^status=PASS phase=install elapsedMs=[2-9]\d{3,} limitSeconds=15 state=pid=\d+ process=exited exitCode=0$'
    Test-InstallerProcess 'exit 23' 15 1 '^status=FAIL phase=install elapsedMs=\d+ limitSeconds=15 state=pid=\d+ process=exited exitCode=23$'
    Test-InstallerProcess 'Start-Sleep -Seconds 30; exit 0' 1 2 '^status=TIMEOUT phase=install elapsedMs=\d+ limitSeconds=1 state=pid=\d+ process=running$'

    Assert-Result {
        Wait-AcceptanceProbe 'gui-ready' 1 { $false } { 'process=running window=False target=synthetic-window' }
    } 2 '^status=TIMEOUT phase=gui-ready elapsedMs=\d+ limitSeconds=1 state=process=running window=False target=synthetic-window$'

    # The desktop wrapper passes a nested probe that calls the caller's original scriptblock.
    function Test-GuiWrapper([scriptblock]$Probe) {
        Wait-AcceptanceProbe 'gui-ready' 1 { & $Probe } { 'process=running window=True' } | Out-Null
    }
    Assert-Result {
        Test-GuiWrapper { $true }
    } 0 '^status=PASS phase=gui-ready elapsedMs=\d+ limitSeconds=1 state=process=running window=True$'

    $sidecar = Start-Process -FilePath $env:ComSpec -ArgumentList '/d /c exit 9' -WindowStyle Hidden -PassThru
    try {
        if (-not $sidecar.WaitForExit(15000)) { throw 'Synthetic sidecar did not exit.' }
        Assert-Result {
            Assert-AcceptanceSidecar $sidecar ([Diagnostics.Stopwatch]::StartNew())
        } 1 '^status=FAIL phase=sidecar-health elapsedMs=\d+ state=pid=\d+ process=exited exitCode=9$'
    }
    finally { Stop-AcceptanceProcess $sidecar 'test-cleanup' 5 }

    Assert-Result {
        Wait-AcceptanceProbe 'sidecar-exit' 1 { $false } { 'process=running' }
    } 2 '^status=TIMEOUT phase=sidecar-exit elapsedMs=\d+ limitSeconds=1 state=process=running$'

    $child = Start-Process -FilePath $env:ComSpec -ArgumentList '/d /c exit 0' -WindowStyle Hidden -PassThru
    try {
        Assert-Result {
            Wait-AcceptanceProbe 'sidecar-exit' 15 { $child.HasExited } { Get-AcceptanceProcessState $child }
        } 0 '^status=PASS phase=sidecar-exit elapsedMs=\d+ limitSeconds=15 state=pid=\d+ process=exited exitCode=0$'
    }
    finally { Stop-AcceptanceProcess $child 'test-cleanup' 5 }

    # Exercise the actual installer entry point with a bad hash before any process can run.
    Set-Content -LiteralPath (Join-Path $testRoot 'Rigarus-Dispatch-x64-setup.exe') -Value 'Synthetic invalid installer'
    New-Item -ItemType File -Path (Join-Path $testRoot 'Test-TauriDesktop.ps1') | Out-Null
    @{ commit = ('a' * 40); installerSha256 = ('0' * 64) } | ConvertTo-Json |
        Set-Content -LiteralPath (Join-Path $testRoot 'build.json')
    $entryPoint = Join-Path $PSScriptRoot 'Test-TauriOfflineInstall.ps1'
    $arguments = @('-NoProfile', '-File', ('"{0}"' -f $entryPoint), '-KitDirectory', ('"{0}"' -f $testRoot),
        '-DiagnosticLog', ('"{0}"' -f $acceptanceLog))
    $entry = Start-Process -FilePath powershell.exe -ArgumentList $arguments -WindowStyle Hidden -PassThru
    try {
        $finished = $entry.WaitForExit(15000)
        $lastEvent = Get-Content -LiteralPath $acceptanceLog -Tail 1
        if (-not $finished -or $entry.ExitCode -ne 1 -or
            $lastEvent -notmatch '^status=FAIL phase=package-integrity .*invalidCommitOrSha256=true$') {
            throw "Integrity check result: finished=$finished exit=$($entry.ExitCode) lastEvent=$lastEvent"
        }
    }
    finally { Stop-AcceptanceProcess $entry 'test-cleanup' 5 }

    # Exercise the real weekly-verifier helpers without an interactive CI desktop.
    $tokens = $null; $parseErrors = $null
    $desktopAst = [Management.Automation.Language.Parser]::ParseFile(
        (Join-Path $PSScriptRoot 'Test-TauriDesktop.ps1'), [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors.Count) { throw 'Desktop verifier does not parse.' }
    foreach ($definition in $desktopAst.EndBlock.Statements) {
        if ($definition -is [Management.Automation.Language.FunctionDefinitionAst] -and
            $definition.Name -in @('Get-SyntheticDateParts', 'Get-SyntheticAssignmentDigest', 'Assert-WeekAssignmentCards')) {
            Invoke-Expression $definition.Extent.Text
        }
    }
    foreach ($example in @(
        @{ Parts = @('Year', 'Month', 'Day'); Expected = 'Year=2026,Month=12,Day=31' },
        @{ Parts = @('Month', 'Day', 'Year'); Expected = 'Month=12,Day=31,Year=2026' },
        @{ Parts = @('Day', 'Month', 'Year'); Expected = 'Day=31,Month=12,Year=2026' }
    )) {
        if (((Get-SyntheticDateParts '2026-12-31' $example.Parts | ForEach-Object { $_.Part + '=' + $_.Digits }) -join ',') -cne $example.Expected) {
            throw 'Date entry did not follow the actual native locale segments.'
        }
    }
    foreach ($bad in @(
        @{ Date = '2027-02-29'; Parts = @('Year', 'Month', 'Day') },
        @{ Date = '2026-12-31'; Parts = @('Month', 'Month', 'Year') },
        @{ Date = '2026-12-31'; Parts = @('Unknown', 'Day', 'Year') }
    )) {
        $rejected = $false
        try { Get-SyntheticDateParts $bad.Date $bad.Parts | Out-Null }
        catch { $rejected = $true }
        if (-not $rejected) { throw 'Invalid date/unsupported segment layout was accepted.' }
    }
    $root = Join-Path $testRoot 'synthetic-profile'
    New-Item -ItemType Directory -Path (Join-Path $root 'data') | Out-Null
    $db = Join-Path $root 'data/rigarus.db'
    Set-Content -LiteralPath $db -Value 'Synthetic digest fixture, not a customer database'
    $before = Get-SyntheticAssignmentDigest
    if ($before -cne (Get-SyntheticAssignmentDigest)) { throw 'Read-only digest changed the fixture.' }
    Set-Content -LiteralPath ($db + '-shm') -Value 'Transient reader locks'
    if ($before -cne (Get-SyntheticAssignmentDigest)) { throw 'Transient SHM locks should not claim a data mutation.' }
    Set-Content -LiteralPath ($db + '-wal') -Value 'Synthetic committed mutation'
    if ($before -ceq (Get-SyntheticAssignmentDigest)) { throw 'WAL mutation escaped the no-write verifier.' }
    $before = Get-SyntheticAssignmentDigest
    Add-Content -LiteralPath $db -Value 'Synthetic main-file mutation'
    if ($before -ceq (Get-SyntheticAssignmentDigest)) { throw 'Main-file mutation escaped the no-write verifier.' }

    function Test-WeeklyCardAssertions {
        function Wait-For([string]$Description, [scriptblock]$Probe) {
            Wait-AcceptanceProbe 'gui-ready' 1 { & $Probe } { 'process=synthetic window=True' }
        }
        function Get-SyntheticAssignmentCards($Window) {
            @('Draft 2, SYN-14-UI, 2026-12-31 PM, Assignment Test Crew',
                'Draft 1, SYN-14-UI, 2026-12-31 AM, Assignment Test Crew') |
                ForEach-Object { [pscustomobject]@{ Current = [pscustomobject]@{ Name = $_ } } }
        }
        $expected = @('Draft 1, SYN-14-UI, 2026-12-31 AM, Assignment Test Crew',
            'Draft 2, SYN-14-UI, 2026-12-31 PM, Assignment Test Crew')
        Assert-WeekAssignmentCards $null $expected
        $timer = [Diagnostics.Stopwatch]::StartNew()
        Assert-Result { Assert-WeekAssignmentCards $null @() } 2 '^status=INFO phase=weekly-card-diagnostic .*actual=Draft 1,.*expected=$'
    }
    Test-WeeklyCardAssertions
    & (Join-Path $PSScriptRoot 'Test-TauriUiaHarness.ps1')
    Write-Host 'PASS: Weekly native date order, invalid dates, read-only/WAL digests and missing-card timeout diagnostics.'
    Write-Host 'PASS: Synthetic offline acceptance harness scenarios.'
}
finally {
    Remove-Item -LiteralPath $testRoot -Recurse -Force
}
