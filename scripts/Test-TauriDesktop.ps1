param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [switch]$RequireOffline,
    [switch]$IncludeProjects
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$Executable = (Resolve-Path -LiteralPath $Executable).Path
if ($RequireOffline -and [Net.NetworkInformation.NetworkInterface]::GetIsNetworkAvailable()) {
    throw 'An active network adapter is present. Disconnect from the network and rerun.'
}

function Wait-For([string]$Description, [scriptblock]$Probe) {
    $timer = [Diagnostics.Stopwatch]::StartNew()
    do {
        $result = & $Probe
        if ($result) { return $result }
        Start-Sleep -Milliseconds 150
    } while ($timer.Elapsed.TotalSeconds -lt 30)
    throw "Timed out waiting for $Description."
}

function Find-Control($Window, $Property, [string]$Value) {
    $condition = New-Object Windows.Automation.PropertyCondition($Property, $Value)
    try {
        Wait-For $Value {
            $Window.FindAll([Windows.Automation.TreeScope]::Descendants, $condition) |
                Select-Object -First 1
        }
    }
    catch {
        $visibleNames = $Window.FindAll([Windows.Automation.TreeScope]::Descendants, [Windows.Automation.Condition]::TrueCondition) |
            ForEach-Object { $_.Current.Name } | Where-Object { $_ }
        throw "$($_.Exception.Message) Visible controls: $($visibleNames -join ', ')"
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
    if (-not $Process.CloseMainWindow() -or -not $Process.WaitForExit(12000)) {
        throw 'The Tauri window did not close cleanly.'
    }
    if ($Process.ExitCode -ne 0) { throw "Unexpected desktop exit code $($Process.ExitCode)." }
}

function Get-Sidecar($Process) {
    Get-CimInstance -ClassName Win32_Process -Filter "ParentProcessId = $($Process.Id) AND Name = 'Rigarus.Sidecar.exe'"
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

$temp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
$runRoot = Join-Path $temp ('rigarus-tauri-smoke-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $runRoot | Out-Null
$root = $runRoot
$name = [Windows.Automation.AutomationElement]::NameProperty
$automationId = [Windows.Automation.AutomationElement]::AutomationIdProperty
$valuePattern = [Windows.Automation.ValuePattern]::Pattern
$process = $null
try {
    $process = Start-Dashboard
    $window = Get-DashboardWindow $process
    Find-Control $window $name 'DEMO-001' | Out-Null
    $note = (Find-Control $window $automationId 'demo-note').GetCurrentPattern($valuePattern)
    if ($note.Current.Value -ne 'Synthetic sample for M0.') { throw 'Initial note did not load.' }
    $firstSidecar = Wait-For 'the local sidecar process' { Get-Sidecar $process }

    $newNote = 'Saved and reopened in the Tauri smoke test.'
    $note.SetValue($newNote)
    $save = Find-Control $window $name 'Save note'
    Wait-For 'Save note to be enabled' { $save.Current.IsEnabled } | Out-Null
    $save.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke()
    Find-Control $window $name 'Note saved.' | Out-Null
    if ($IncludeProjects) { Test-Projects $window }
    Close-Dashboard $process
    if (Get-Process -Id $firstSidecar.ProcessId -ErrorAction SilentlyContinue) {
        throw 'The sidecar remained running after closing the Tauri window.'
    }
    $process.Dispose()

    $process = Start-Dashboard
    $window = Get-DashboardWindow $process
    $note = (Find-Control $window $automationId 'demo-note').GetCurrentPattern($valuePattern)
    if ($note.Current.Value -ne $newNote) { throw 'Saved note did not survive a desktop restart.' }
    if ($IncludeProjects) {
        Invoke-Button $window 'Projects'
        Find-Control $window $name ("DEMO-26001 {0} Edited synthetic yard" -f [char]0x00B7) | Out-Null
        Find-Control $window $name 'Small' | Out-Null
        Write-Host 'PASS: Tauri Project Master created, validated, edited, searched and reopened a synthetic project with a work item.'
    }
    Close-Dashboard $process

    # A file at the expected directory path induces a synthetic startup failure.
    $process.Dispose()
    $process = $null
    $root = Join-Path $root 'startup-failure'
    New-Item -ItemType Directory -Path $root | Out-Null
    New-Item -ItemType File -Path (Join-Path $root 'data') | Out-Null
    $process = Start-Dashboard
    $window = Get-DashboardWindow $process
    Find-Control $window $name 'Unable to open the local database. Check folder permissions and close other Rigarus windows.' | Out-Null
    Find-Control $window $name 'Retry' | Out-Null
    Close-Dashboard $process
    if ($RequireOffline) { Write-Host 'PASS: Windows reported no active network adapter before launch.' }
    Write-Host 'PASS: Tauri saved and reopened a synthetic note, stopped the sidecar, and displayed an actionable startup error.'
}
finally {
    if ($process) {
        if (-not $process.HasExited) {
            $process.Kill()
            $process.WaitForExit()
        }
        $process.Dispose()
    }
    $resolved = [IO.Path]::GetFullPath($runRoot)
    if ($resolved.StartsWith($temp + 'rigarus-tauri-smoke-', [StringComparison]::OrdinalIgnoreCase) -and
        (Test-Path -LiteralPath $resolved -PathType Container)) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
