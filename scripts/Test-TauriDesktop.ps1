param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [switch]$RequireOffline,
    [switch]$IncludeProjects,
    [ValidateSet('Default', 'SlowVm')]
    [string]$Profile = 'Default',
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

function Wait-For([string]$Description, [scriptblock]$Probe) {
    $timer = [Diagnostics.Stopwatch]::StartNew()
    # Descriptions are fixed synthetic test labels, never text read from the desktop.
    $target = $Description -replace '[^a-zA-Z0-9_-]', '_'
    Write-AcceptanceEvent 'START' 'gui-ready' $timer $waits.GuiTimeoutSeconds "target=$target"
    Wait-AcceptanceProbe 'gui-ready' $waits.GuiTimeoutSeconds {
        if ($process.HasExited) {
            Stop-Acceptance 'FAIL' 'gui-ready' $timer $waits.GuiTimeoutSeconds (Get-AcceptanceProcessState $process)
        }
        if ($sidecar) { Assert-AcceptanceSidecar $sidecar $timer }
        & $Probe
    } {
        $state = Get-AcceptanceProcessState $process
        $hasWindow = $process.MainWindowHandle -ne [IntPtr]::Zero
        "$state target=$target window=$hasWindow"
    } $timer
}

function Find-Control($Window, $Property, [string]$Value) {
    $condition = New-Object Windows.Automation.PropertyCondition($Property, $Value)
    Wait-For $Value {
        $Window.FindFirst([Windows.Automation.TreeScope]::Descendants, $condition)
    }
}

function Start-Dashboard {
    $start = New-Object Diagnostics.ProcessStartInfo
    $start.FileName = $Executable
    $start.WorkingDirectory = Split-Path -Parent $Executable
    $start.UseShellExecute = $false
    $start.EnvironmentVariables['RIGARUS_SMOKE_DATA_ROOT'] = $root
    $start.EnvironmentVariables['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = '--force-renderer-accessibility'
    [Diagnostics.Process]::Start($start)
}

function Get-DashboardWindow($Process) {
    Wait-For 'the Tauri window' {
        $Process.Refresh()
        if ($Process.HasExited) { throw "Desktop exited with code $($Process.ExitCode)." }
        if ($Process.MainWindowHandle -ne [IntPtr]::Zero) {
            $window = [Windows.Automation.AutomationElement]::FromHandle($Process.MainWindowHandle)
            if ($window.Current.Name -eq 'Rigarus Offline Dispatch Scheduler') { $window }
        }
    }
}

function Close-Dashboard($Process) {
    $timer = [Diagnostics.Stopwatch]::StartNew()
    if ($sidecar) { Assert-AcceptanceSidecar $sidecar $timer }
    Write-AcceptanceEvent 'START' 'desktop-exit' $timer $waits.ExitTimeoutSeconds (Get-AcceptanceProcessState $Process)
    if (-not $Process.CloseMainWindow()) {
        Stop-Acceptance 'FAIL' 'desktop-exit' $timer $waits.ExitTimeoutSeconds ((Get-AcceptanceProcessState $Process) + ' closeRequested=false')
    }
    Wait-AcceptanceProcess $Process 'desktop-exit' $waits.ExitTimeoutSeconds $timer
    if ($sidecar) {
        Write-AcceptanceEvent 'START' 'sidecar-exit' $timer $waits.ExitTimeoutSeconds (Get-AcceptanceProcessState $sidecar)
        Wait-AcceptanceProbe 'sidecar-exit' $waits.ExitTimeoutSeconds { $sidecar.HasExited } {
            Get-AcceptanceProcessState $sidecar
        } $timer | Out-Null
    }
}

function Get-Sidecar($Process) {
    $child = Get-CimInstance -ClassName Win32_Process -OperationTimeoutSec 5 -Filter "ParentProcessId = $($Process.Id) AND Name = 'Rigarus.Sidecar.exe'" |
        Select-Object -First 1
    if ($child) { Get-Process -Id $child.ProcessId -ErrorAction SilentlyContinue }
}

function Invoke-Button($Window, [string]$Label) {
    $button = Find-Control $Window $name $Label
    Wait-For "$Label to be enabled" { $button.Current.IsEnabled } | Out-Null
    $button.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke()
}

function Set-Field($Window, [string]$Id, [string]$Value) {
    (Find-Control $Window $automationId $Id).GetCurrentPattern($valuePattern).SetValue($Value)
}

function Test-Projects($Window) {
    Invoke-Button $Window 'Projects'
    Invoke-Button $Window 'New project'
    Set-Field $Window 'job_number' 'DEMO-26001'
    Set-Field $Window 'site_id' '0042'
    Set-Field $Window 'site_name' 'Synthetic yard'
    Invoke-Button $Window 'Save project'
    Find-Control $Window $name ("DEMO-26001 {0} Synthetic yard" -f [char]0x00B7) | Out-Null
    Find-Control $Window $name 'No work items yet.' | Out-Null

    Invoke-Button $Window 'New project'
    Set-Field $Window 'job_number' 'demo-26001'
    Set-Field $Window 'site_id' '0099'
    Set-Field $Window 'site_name' 'Duplicate synthetic site'
    Invoke-Button $Window 'Save project'
    Find-Control $Window $name 'That Job # already belongs to another project.' | Out-Null
    Invoke-Button $Window 'Cancel'

    Invoke-Button $Window 'Edit project'
    Set-Field $Window 'site_name' 'Edited synthetic yard'
    Invoke-Button $Window 'Add work item'
    Set-Field $Window 'half-days-0' '1.5'
    Invoke-Button $Window 'Save project'
    Find-Control $Window $name 'Work item 1 needs a positive whole number for crews and estimated half-days.' | Out-Null
    Set-Field $Window 'half-days-0' '3'
    Invoke-Button $Window 'Save project'
    Find-Control $Window $name ("DEMO-26001 {0} Edited synthetic yard" -f [char]0x00B7) | Out-Null

    Set-Field $Window 'project-search' '0042'
    Invoke-Button $Window 'Search'
    Find-Control $Window $name '1 project' | Out-Null
    Set-Field $Window 'project-search' 'unmatched'
    Invoke-Button $Window 'Search'
    Find-Control $Window $name 'No projects match your search.' | Out-Null
}

Write-Host "Diagnostic log: $acceptanceLog"
Write-AcceptanceEvent 'INFO' 'gui-configuration' $null 0 "profile=$Profile guiSeconds=$($waits.GuiTimeoutSeconds) exitSeconds=$($waits.ExitTimeoutSeconds)"
$timer = [Diagnostics.Stopwatch]::StartNew()
$process = $null
$sidecar = $null
$runRoot = $null
$exitCode = 0
$phase = 'desktop-launch'
try {
    if ($RequireOffline -and [Net.NetworkInformation.NetworkInterface]::GetIsNetworkAvailable()) {
        Stop-Acceptance 'BLOCKED' 'environment' $timer 0 'activeNetworkAdapter=true'
    }
    Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
    $Executable = (Resolve-Path -LiteralPath $Executable).Path
    $runRoot = Join-Path ([IO.Path]::GetTempPath()) ('rigarus-tauri-smoke-' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $runRoot | Out-Null
    $root = $runRoot
    $name = [Windows.Automation.AutomationElement]::NameProperty
    $automationId = [Windows.Automation.AutomationElement]::AutomationIdProperty
    $valuePattern = [Windows.Automation.ValuePattern]::Pattern

    $process = Start-Dashboard
    Write-AcceptanceEvent 'START' $phase $timer 0 (Get-AcceptanceProcessState $process)
    $phase = 'desktop-functional-checks'
    $window = Get-DashboardWindow $process
    Find-Control $window $name 'DEMO-001' | Out-Null
    $sidecar = Wait-For 'sidecar-process' { Get-Sidecar $process }
    $note = (Find-Control $window $automationId 'demo-note').GetCurrentPattern($valuePattern)
    if ($note.Current.Value -ne 'Synthetic sample for M0.') {
        Stop-Acceptance 'FAIL' 'initial-note' $timer 0 'fixtureMismatch=true'
    }

    $newNote = 'Saved and reopened in the Tauri smoke test.'
    $note.SetValue($newNote)
    Invoke-Button $window 'Save note'
    Find-Control $window $name 'Note saved.' | Out-Null
    if ($IncludeProjects) { Test-Projects $window }
    Close-Dashboard $process
    $process.Dispose()
    $process = $null
    $sidecar.Dispose()
    $sidecar = $null

    $process = Start-Dashboard
    Write-AcceptanceEvent 'START' 'desktop-reopen' $timer 0 (Get-AcceptanceProcessState $process)
    $window = Get-DashboardWindow $process
    Find-Control $window $name 'DEMO-001' | Out-Null
    $sidecar = Wait-For 'sidecar-process' { Get-Sidecar $process }
    $note = (Find-Control $window $automationId 'demo-note').GetCurrentPattern($valuePattern)
    if ($note.Current.Value -ne $newNote) {
        Stop-Acceptance 'FAIL' 'note-reopen' $timer 0 'savedNoteMismatch=true'
    }
    if ($IncludeProjects) {
        Invoke-Button $window 'Projects'
        Find-Control $window $name ("DEMO-26001 {0} Edited synthetic yard" -f [char]0x00B7) | Out-Null
        Find-Control $window $name 'Small' | Out-Null
        Write-AcceptanceEvent 'PASS' 'project-master' $timer 0 'syntheticProjectAndWorkItem=reopened'
    }
    Close-Dashboard $process
    $process.Dispose()
    $process = $null
    $sidecar.Dispose()
    $sidecar = $null

    # A file at the expected directory path induces a synthetic startup failure.
    $phase = 'startup-error'
    $root = Join-Path $runRoot 'startup-failure'
    New-Item -ItemType Directory -Path $root | Out-Null
    New-Item -ItemType File -Path (Join-Path $root 'data') | Out-Null
    $process = Start-Dashboard
    $window = Get-DashboardWindow $process
    Find-Control $window $name 'Unable to open the local database. Check folder permissions and close other Rigarus windows.' | Out-Null
    Find-Control $window $name 'Retry' | Out-Null
    Close-Dashboard $process
    Write-AcceptanceEvent 'PASS' 'desktop-smoke' $timer 0 'note=reopened sidecar=exited startupError=displayed'
}
catch { $exitCode = Get-AcceptanceExitCode $_ $phase $timer }
finally {
    Stop-AcceptanceProcess $process 'desktop-cleanup' $waits.ExitTimeoutSeconds
    Stop-AcceptanceProcess $sidecar 'sidecar-cleanup' $waits.ExitTimeoutSeconds
    if ($runRoot -and (Test-Path -LiteralPath $runRoot -PathType Container)) {
        Remove-Item -LiteralPath $runRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
exit $exitCode
