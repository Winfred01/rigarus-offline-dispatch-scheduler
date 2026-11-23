param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [switch]$RequireOffline,
    [switch]$IncludeProjects,
    [switch]$IncludeProjectValidation,
    [switch]$IncludeProjectSorting,
    [switch]$IncludeBulkProjects,
    [switch]$IncludeCrews,
    [switch]$IncludeForemen,
    [switch]$IncludeAssignments,
    [switch]$IncludeMultiDay,
    [switch]$IncludeStaffing,
    [switch]$IncludeAvailability,
    [switch]$IncludeEmployeeWeek,
    [switch]$IncludeWorkingCalendars,
    [switch]$ReproduceCrewChoice,
    [switch]$PreserveSyntheticProfile,
    [ValidateSet('Default', 'SlowVm')]
    [string]$Profile = 'Default',
    [ValidateRange(1, 300)]
    [int]$GuiTimeoutSeconds,
    [ValidateRange(1, 180)]
    [int]$ExitTimeoutSeconds,
    [string]$DiagnosticLog,
    [string]$UiaDiagnosticLog
)

$ErrorActionPreference = 'Stop'
Write-Host ('VerifierSourceSha256=' + (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash)
if ($IncludeMultiDay) { $IncludeAssignments = $true }
if ($IncludeWorkingCalendars) { $IncludeAssignments = $true }
if ($IncludeEmployeeWeek) { $IncludeAvailability = $true }
if ($IncludeAvailability) { $IncludeStaffing = $true }
if ($IncludeStaffing) { $IncludeAssignments = $true; $IncludeCrews = $true }
$staffingWorkerAName = if ($IncludeForemen) { 'Synthetic Foreman A' } else { 'Synthetic Staffing A' }
$staffingWorkerBName = if ($IncludeForemen) { 'Synthetic Foreman B renamed' } else { 'Synthetic Staffing B' }
. (Join-Path $PSScriptRoot 'TauriAcceptanceSupport.ps1')
. (Join-Path $PSScriptRoot 'TauriUiaDiagnostics.ps1')
$waits = Get-AcceptanceWaits $Profile $PSBoundParameters
$acceptanceLog = Get-AcceptanceLogPath $DiagnosticLog
$uiaDiagnosticLog = Get-AcceptanceLogPath $(if ($UiaDiagnosticLog) { $UiaDiagnosticLog } else { $acceptanceLog + '.uia.jsonl' })
$uiaLastOperation = 'desktop-launch'; $uiaLastControl = $null; $uiaLastOption = $null

function Wait-For([string]$Description, [scriptblock]$Probe) {
    $timer = [Diagnostics.Stopwatch]::StartNew()
    # Descriptions are fixed synthetic test labels, never text read from the desktop.
    $target = $Description -replace '[^a-zA-Z0-9_-]', '_'
    Write-AcceptanceEvent 'START' 'gui-ready' $timer $waits.GuiTimeoutSeconds "target=$target"
    Wait-AcceptanceProbe 'gui-ready' $waits.GuiTimeoutSeconds {
        if ($process.HasExited) {
            Stop-Acceptance 'FAIL' 'gui-ready' $timer $waits.GuiTimeoutSeconds (Get-AcceptanceProcessState $process)
        }
        Restore-AcceptanceWindow $process
        if ($sidecar) { Assert-AcceptanceSidecar $sidecar $timer }
        & $Probe
    } {
        $state = Get-AcceptanceProcessState $process
        $hasWindow = $process.MainWindowHandle -ne [IntPtr]::Zero
        "$state target=$target window=$hasWindow"
    } $timer
}

function Find-Control($Window, $Property, [string]$Value, [switch]$Button) {
    $condition = New-Object Windows.Automation.PropertyCondition($Property, $Value)
    if ($Button) {
        $buttonCondition = [Windows.Automation.PropertyCondition]::new(
            [Windows.Automation.AutomationElement]::ControlTypeProperty, [Windows.Automation.ControlType]::Button)
        $condition = [Windows.Automation.AndCondition]::new($condition, $buttonCondition)
    }
    Wait-For $Value {
        $Window.FindAll([Windows.Automation.TreeScope]::Descendants, $condition) |
            Select-Object -First 1
    }
}

function Start-Dashboard {
    $script:uiaOwnedHandle = [IntPtr]::Zero
    $script:uiaOwnedWindow = $null
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
            if ($window.Current.Name -eq 'Rigarus Offline Dispatch Scheduler') {
                if (-not ('RigarusAcceptanceWindow' -as [type])) {
                    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class RigarusAcceptanceWindow {
    [DllImport("user32.dll")] public static extern uint GetDpiForWindow(IntPtr window);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr window);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr window, int command);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr window);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);
}
'@
                }
                $script:uiaOwnedHandle = $Process.MainWindowHandle
                $script:uiaOwnedWindow = $window
                Restore-AcceptanceWindow $Process
                if (-not [RigarusAcceptanceWindow]::IsWindowVisible($Process.MainWindowHandle)) { return $null }
                if ($IncludeAssignments -or $ReproduceCrewChoice) {
                    $transform = $window.GetCurrentPattern([Windows.Automation.TransformPattern]::Pattern)
                    if (-not $transform.Current.CanResize) { throw 'Weekly smoke requires a resizable test window.' }
                    # TransformPattern uses physical pixels; Tauri sizes use DIPs.
                    $dpi = [RigarusAcceptanceWindow]::GetDpiForWindow($Process.MainWindowHandle)
                    if ($dpi -lt 96 -or $dpi -gt 480) { throw 'Unsupported test-window DPI.' }
                    $transform.Resize(1000 * $dpi / 96, 720 * $dpi / 96)
                }
                $window
            }
        }
    }
}

function Restore-AcceptanceWindow($Process) {
    if (-not $script:uiaOwnedHandle -or $script:uiaOwnedHandle -eq [IntPtr]::Zero) { return }
    [uint32]$owner = 0
    [RigarusAcceptanceWindow]::GetWindowThreadProcessId($script:uiaOwnedHandle, [ref]$owner) | Out-Null
    if ($owner -ne $Process.Id) { throw 'Verifier window ownership changed.' }
    # Startup visibility may change after the title first appears. Recheck on
    # every bounded GUI probe; never restore a window from another process.
    if (-not [RigarusAcceptanceWindow]::IsWindowVisible($script:uiaOwnedHandle) -or
        [RigarusAcceptanceWindow]::IsIconic($script:uiaOwnedHandle)) {
        Write-UiaOperation 'desktop:restore-owned-window' 'before' $script:uiaOwnedWindow $null
        [RigarusAcceptanceWindow]::ShowWindow($script:uiaOwnedHandle, 9) | Out-Null
        Write-UiaOperation 'desktop:restore-owned-window' 'after' $script:uiaOwnedWindow $null
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
    if ($child) {
        $observed = Get-Process -Id $child.ProcessId -ErrorAction SilentlyContinue
        if ($observed) {
            # Retain the handle so HasExited and ExitCode remain observable after shutdown.
            $null = $observed.Handle
            $observed
        }
    }
}

function Invoke-Button($Window, [string]$Label) {
    # Keep historical master-data smoke actions usable after the #16 module rail.
    if ($Label -eq 'Projects') { Invoke-Button $Window 'Project Management'; return }
    if ($Label -eq 'Rigs') { Invoke-Button $Window 'Items'; return }
    if ($Label -eq 'Crews' -or $Label -eq 'Employees') { Invoke-Button $Window 'People' }

    $button = Find-Control $Window $name $Label -Button
    Wait-For "$Label to be enabled" { $button.Current.IsEnabled } | Out-Null
    $button.SetFocus()
    if ($Label -match '^Copy (TSV|CSV) example$') {
        # Clipboard writes require an actual keyboard/pointer user gesture.
        [Windows.Forms.SendKeys]::SendWait('{ENTER}')
        return
    }
    $pattern = $null
    if ($button.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern, [ref]$pattern)) {
        $pattern.Invoke()
    }
    elseif ($button.TryGetCurrentPattern([Windows.Automation.ExpandCollapsePattern]::Pattern, [ref]$pattern)) {
        # WebView2 exposes native popover buttons as expand/collapse controls.
        if ($pattern.Current.ExpandCollapseState -eq [Windows.Automation.ExpandCollapseState]::Expanded) { $pattern.Collapse() }
        else { $pattern.Expand() }
    }
    elseif ($button.TryGetCurrentPattern([Windows.Automation.TogglePattern]::Pattern, [ref]$pattern)) {
        # Schedule cards expose aria-pressed through native Toggle, not Invoke.
        $pattern.Toggle()
    }
    else { throw 'Synthetic button has no supported action pattern.' }
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
    Find-Control $Window $name 'Estimated half-days must be a whole number of at least 1.' | Out-Null
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

function Test-Crews($Window) {
    Invoke-Button $Window 'Crews'
    Invoke-Button $Window 'New crew'
    Set-Field $Window 'crew-name' 'Synthetic Civil 01'
    Invoke-Button $Window 'Save crew'
    Find-Control $Window $name 'Crew saved.' | Out-Null
    Invoke-Button $Window 'Edit Synthetic Civil 01'
    Set-Field $Window 'crew-name' 'Synthetic Civil 02'
    Invoke-Button $Window 'Save crew'
    Find-Control $Window $name 'Edit Synthetic Civil 02' | Out-Null
    Set-Field $Window 'crew-search' 'unknown-crew'
    Invoke-Button $Window 'Search'
    Find-Control $Window $name 'No crews match your search.' | Out-Null
    Set-Field $Window 'crew-search' 'civil 02'
    Invoke-Button $Window 'Search'
    Find-Control $Window $name 'Edit Synthetic Civil 02' | Out-Null
}

function Select-FieldIndex($Window, [string]$Id, [int]$Index) {
    Add-Type -AssemblyName System.Windows.Forms
    $control = Find-Control $Window $automationId $Id
    $control.SetFocus()
    Start-Sleep -Milliseconds 100
    [Windows.Forms.SendKeys]::SendWait('{HOME}')
    Start-Sleep -Milliseconds 100
    for ($i = 0; $i -lt $Index; $i++) { [Windows.Forms.SendKeys]::SendWait('{DOWN}'); Start-Sleep -Milliseconds 100 }
    [Windows.Forms.SendKeys]::SendWait('{ENTER}')
    Start-Sleep -Milliseconds 100
}

function Open-SyntheticForeman($Window) {
    Invoke-Button $Window 'Crews'
    Invoke-Button $Window 'Foreman for Synthetic Civil 02'
    Find-Control $Window $automationId 'foreman-employee' | Out-Null
}

function Test-Foremen($Window) {
    Invoke-Button $Window 'Crews'
    Invoke-Button $Window 'New crew'
    Set-Field $Window 'crew-name' 'Synthetic Tower Home'
    Select-FieldIndex $Window 'crew-type' 1
    Invoke-Button $Window 'Save crew'
    Find-Control $Window $name 'Crew saved.' | Out-Null
    foreach ($person in @('Synthetic Foreman A', 'Synthetic Foreman B')) {
        Invoke-Button $Window 'Employees'
        Invoke-Button $Window 'New employee'
        Set-Field $Window 'employee-name' $person
        Select-FieldIndex $Window 'employee-home-crew' 2
        Select-FieldIndex $Window 'employee-skill' 1
        Select-FieldIndex $Window 'employee-foreman-eligible' 1
        Invoke-Button $Window 'Save employee'
        Find-Control $Window $name 'Employee saved.' | Out-Null
    }
    Open-SyntheticForeman $Window
    Find-Control $Window $name 'No Foreman changes yet.' | Out-Null
    Select-FieldIndex $Window 'foreman-employee' 1
    Invoke-Button $Window 'Save Foreman'
    Find-Control $Window $name 'Foreman saved.' | Out-Null
    Assert-TableColumn $Window 'Foreman change records' 2 @('Synthetic Foreman A (#1)')
    Select-FieldIndex $Window 'foreman-employee' 2
    Invoke-Button $Window 'Back to Crews'
    Wait-For 'foreman-return-focus' {
        (Find-Control $Window $automationId 'crew-foreman-1').Current.HasKeyboardFocus
    } | Out-Null
    Open-SyntheticForeman $Window
    Assert-TableColumn $Window 'Foreman change records' 2 @('Synthetic Foreman A (#1)')
    Select-FieldIndex $Window 'foreman-employee' 2
    Invoke-Button $Window 'Save Foreman'
    Find-Control $Window $name 'Foreman saved.' | Out-Null
    Assert-TableColumn $Window 'Foreman change records' 2 @('Synthetic Foreman B (#2)', 'Synthetic Foreman A (#1)')
    Invoke-Button $Window 'Back to Crews'
    Invoke-Button $Window 'Employees'
    Invoke-Button $Window 'Edit Synthetic Foreman B'
    Set-Field $Window 'employee-name' 'Synthetic Foreman B renamed'
    Select-FieldIndex $Window 'employee-active' 1
    Select-FieldIndex $Window 'employee-foreman-eligible' 0
    Invoke-Button $Window 'Save employee'
    Find-Control $Window $name 'Employee saved.' | Out-Null
    Open-SyntheticForeman $Window
    Assert-TableColumn $Window 'Foreman change records' 2 @('Synthetic Foreman B (#2)', 'Synthetic Foreman A (#1)')
    $retained = Find-Control $Window $automationId 'foreman-current'
    if ($retained.Current.Name -notmatch 'Synthetic Foreman B renamed.*Inactive.*No longer marked Foreman eligible') {
        throw 'Current Foreman status or retained ID is missing.'
    }
    Select-FieldIndex $Window 'foreman-employee' 0
    Invoke-Button $Window 'Save Foreman'
    Find-Control $Window $name 'Foreman saved.' | Out-Null
    Assert-TableColumn $Window 'Foreman change records' 2 @('Unassigned', 'Synthetic Foreman B (#2)', 'Synthetic Foreman A (#1)')
    Select-FieldIndex $Window 'foreman-employee' 1
    Invoke-Button $Window 'Save Foreman'
    Find-Control $Window $name 'Foreman saved.' | Out-Null
    Assert-TableColumn $Window 'Foreman change records' 2 @('Synthetic Foreman A (#1)', 'Unassigned', 'Synthetic Foreman B (#2)', 'Synthetic Foreman A (#1)')
    Invoke-Button $Window 'Back to Crews'
    Invoke-Button $Window 'Employees'
    Find-Control $Window $name 'Edit Synthetic Foreman A' | Out-Null
    Assert-TableColumn $Window 'Employee records' 1 @('Synthetic Tower Home (Tower #2)', 'Synthetic Tower Home (Tower #2)')
    Assert-TableColumn $Window 'Employee records' 4 @('Unverified', 'Unverified')
    Write-AcceptanceEvent 'PASS' 'foreman-lifecycle' $timer 0 'appoint=passed replace=passed cancel=preserved clear=passed snapshots=preserved homeCrew=unchanged retainedInactive=visible keyboard=passed'
}

function Assert-InputFocus($Window, [string]$Id) {
    Wait-For 'invalid-field-visible-and-focused' {
        $control = Find-Control $Window $automationId $Id
        $control.Current.HasKeyboardFocus -and -not $control.Current.IsOffscreen
    } | Out-Null
}

function Assert-SyntheticTextContains($Window, [string]$SyntheticNeedle) {
    Wait-For 'synthetic-visible-text' {
        # WebView2 can coalesce nested roster text into the row-header accessible
        # name rather than exposing an independent StaticText element.
        @($Window.FindAll([Windows.Automation.TreeScope]::Descendants, [Windows.Automation.Condition]::TrueCondition) |
            Where-Object { ([string]$_.Current.Name).Contains($SyntheticNeedle) }).Count -gt 0
    } | Out-Null
}

function Open-SyntheticAssignment($Window, [int]$WorkItemId) {
    Invoke-Button $Window 'Projects'
    Set-Field $Window 'project-search' 'SYN-14-UI'
    Invoke-Button $Window 'Search'
    Invoke-Button $Window 'SYN-14-UI'
    Invoke-Button $Window ('Assign Work Item ' + $WorkItemId)
    Find-Control $Window $automationId 'assignment-date' | Out-Null
}

function Select-AssignmentChoice($Window, [string]$Id, [string]$Keys, [string]$ExpectedChoice) {
    $context = [pscustomobject]@{ operation = "choice:${Id}:read"; control = $null; option = $null; traced = $false; retries = 0 }
    $choiceTimer = [Diagnostics.Stopwatch]::StartNew()
    $idCondition = [Windows.Automation.PropertyCondition]::new($automationId, $Id)
    $optionCondition = [Windows.Automation.PropertyCondition]::new(
        [Windows.Automation.AutomationElement]::ControlTypeProperty, [Windows.Automation.ControlType]::ListItem)
    try {
        # One bounded wait covers the whole interaction. Each probe resolves the
        # live control/pattern again; a committed choice is verified before any
        # repeated selection. No API or persistent write occurs in this loop.
        Wait-For 'assignment-choice-committed' {
            Invoke-UiaTransientProbe {
                $context.operation = "choice:${Id}:read"
                $controls = @($Window.FindAll([Windows.Automation.TreeScope]::Descendants, $idCondition))
                if ($controls.Count -gt 1) { throw 'Synthetic choice control is ambiguous.' }
                if (-not $controls.Count) { return $false }
                $control = $controls[0]; $context.control = $control; $context.option = $null
                if (-not $control.Current.IsEnabled) { return $false }
                if (-not $context.traced) {
                    Write-UiaOperation $context.operation 'before' $Window $control
                    $context.traced = $true
                }
                $value = $null
                if (-not $control.TryGetCurrentPattern($valuePattern, [ref]$value)) {
                    throw [NotSupportedException]::new('Synthetic choice does not expose Value.')
                }
                $observed = [string]$value.Current.Value
                $expand = $null
                if (-not $control.TryGetCurrentPattern([Windows.Automation.ExpandCollapsePattern]::Pattern, [ref]$expand)) {
                    throw [NotSupportedException]::new('Synthetic choice does not expose ExpandCollapse.')
                }
                if (Test-UiaChoiceLabel $observed $ExpectedChoice) {
                    if ($expand.Current.ExpandCollapseState -eq [Windows.Automation.ExpandCollapseState]::Expanded) {
                        $context.operation = "choice:${Id}:collapse"; $expand.Collapse(); return $false
                    }
                    return $true
                }
                if ($expand.Current.ExpandCollapseState -ne [Windows.Automation.ExpandCollapseState]::Expanded) {
                    $context.operation = "choice:${Id}:focus"
                    $scrollItem = $null
                    if ($control.TryGetCurrentPattern([Windows.Automation.ScrollItemPattern]::Pattern, [ref]$scrollItem)) { $scrollItem.ScrollIntoView() }
                    $control.SetFocus()
                    $context.operation = "choice:${Id}:expand"; $expand.Expand(); return $false
                }
                $context.operation = "choice:${Id}:options"
                $options = @($Window.FindAll([Windows.Automation.TreeScope]::Descendants, $optionCondition) |
                    Where-Object { Test-UiaChoiceLabel ([string]$_.Current.Name) $ExpectedChoice })
                if ($options.Count -gt 1) { throw 'Synthetic choice is ambiguous.' }
                if (-not $options.Count) { return $false }
                $option = $options[0]; $context.option = $option
                if (-not $option.Current.IsEnabled) { return $false }
                $selection = $null
                if (-not $option.TryGetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern, [ref]$selection)) { return $false }
                $context.operation = "choice:${Id}:select"; $selection.Select()
                # Selection may replace popup providers. Read the live value and
                # obtain a fresh collapse pattern on the next bounded probe.
                $false
            } {
                param($errorRecord)
                $context.retries++
                Write-UiaFailure $errorRecord $context.operation $Window $context.control $context.option 'retrying'
                Write-AcceptanceEvent 'INFO' 'uia-transient' $choiceTimer $waits.GuiTimeoutSeconds "target=$Id attempt=$($context.retries)"
            }
        } | Out-Null
        Write-UiaOperation "choice:${Id}:verified" 'after' $Window $context.control $context.option
    }
    catch {
        $script:uiaLastOperation = $context.operation; $script:uiaLastControl = $context.control; $script:uiaLastOption = $context.option
        Write-UiaFailure $_ $context.operation $Window $context.control $context.option
        throw
    }
}

function Test-CrewChoiceReproduction($Window) {
    foreach ($label in @('Synthetic Choice Crew A', 'Synthetic Choice Crew B')) {
        Invoke-Button $Window 'Crews'; Invoke-Button $Window 'New crew'
        Set-Field $Window 'crew-name' $label; Invoke-Button $Window 'Save crew'
        Find-Control $Window $name 'Crew saved.' | Out-Null
    }
    Invoke-Button $Window 'Projects'; Invoke-Button $Window 'New project'
    Set-Field $Window 'job_number' 'SYN-14-UI'; Set-Field $Window 'site_id' '0007'
    Set-Field $Window 'site_name' 'Synthetic Crew selector reproduction'
    Invoke-Button $Window 'Add work item'; Invoke-Button $Window 'Save project'
    $table = Find-Control $Window $name 'Project work items'
    $condition = [Windows.Automation.PropertyCondition]::new(
        [Windows.Automation.AutomationElement]::ControlTypeProperty, [Windows.Automation.ControlType]::Button)
    $assign = $table.GetCurrentPattern([Windows.Automation.GridPattern]::Pattern).GetItem(1, 3).
        FindFirst([Windows.Automation.TreeScope]::Descendants, $condition)
    $workItem = [int]($assign.Current.Name -replace '^Assign Work Item ', '')
    Open-SyntheticAssignment $Window $workItem
    Select-AssignmentChoice $Window 'assignment-crew' '' 'Synthetic Choice Crew A'
    Set-Field $Window 'assignment-date' '2026-12-31'
    Set-Field $Window 'assignment-notes' 'Synthetic first AM Draft'
    Invoke-Button $Window 'Save to Draft'; Close-AssignmentDetails $Window 1
    Open-SyntheticAssignment $Window $workItem
    Select-AssignmentChoice $Window 'assignment-crew' '' 'Synthetic Choice Crew A'
    Select-AssignmentChoice $Window 'assignment-crew' '' 'Synthetic Choice Crew B'
    Invoke-Button $Window 'Cancel'
    Write-AcceptanceEvent 'PASS' 'crew-choice-reproduction' $timer 0 'crews=2 workItems=1 firstAM=saved repeatedChoice=verified alternateCrew=verified'
}

function Get-SyntheticDateParts([string]$Date, [string[]]$Parts) {
    $calendarDate = [DateTime]::ParseExact($Date, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    if ($Parts.Count -ne 3 -or (($Parts | Sort-Object) -join ',') -cne 'Day,Month,Year') {
        throw 'Unsupported date control segments; expected Year, Month and Day exactly once.'
    }
    $fields = @{ Year = $calendarDate.ToString('yyyy'); Month = $calendarDate.ToString('MM'); Day = $calendarDate.ToString('dd') }
    @($Parts | ForEach-Object { [pscustomobject]@{ Part = $_; Digits = $fields[$_] } })
}

function Show-SyntheticAssignmentDate($Window, [string]$Date) {
    $dateControl = Find-Control $Window $automationId 'schedule-date'
    Wait-For 'schedule-date-enabled' { $dateControl.Current.IsEnabled } | Out-Null
    $condition = [Windows.Automation.PropertyCondition]::new(
        [Windows.Automation.AutomationElement]::ControlTypeProperty,
        [Windows.Automation.ControlType]::Spinner)
    $parts = @($dateControl.FindAll([Windows.Automation.TreeScope]::Descendants, $condition) |
        ForEach-Object { ([string]$_.Current.Name -split ' ')[0] })
    $dateParts = Get-SyntheticDateParts $Date $parts
    # WebView2 advertises ValuePattern here but SetValue silently keeps the old date.
    # Type only validated digits into the activated test window, in its actual locale order.
    Add-Type -AssemblyName Microsoft.VisualBasic, System.Windows.Forms
    if (-not ('RigarusAcceptanceInput' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class RigarusAcceptanceInput {
    [StructLayout(LayoutKind.Sequential)] public struct Point { public int X,Y; }
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern IntPtr WindowFromPhysicalPoint(Point point);
    [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr window,uint flag);
    [DllImport("user32.dll")] public static extern bool SetPhysicalCursorPos(int x,int y);
    [DllImport("user32.dll")] public static extern bool GetPhysicalCursorPos(out Point point);
    [DllImport("user32.dll")] static extern void mouse_event(uint flags,uint x,uint y,uint data,UIntPtr extra);
    public static bool ClickOwned(int x,int y,IntPtr owner) {
        if(owner==IntPtr.Zero)return false;
        var point=new Point { X=x,Y=y };
        if(GetForegroundWindow()!=owner || GetAncestor(WindowFromPhysicalPoint(point),2)!=owner)return false;
        if(!SetPhysicalCursorPos(x,y))return false;
        mouse_event(2,0,0,0,UIntPtr.Zero);mouse_event(4,0,0,0,UIntPtr.Zero);return true;
    }
}
'@
    }
    [Microsoft.VisualBasic.Interaction]::AppActivate($process.Id)
    $originalPointer = New-Object RigarusAcceptanceInput+Point
    $null = [RigarusAcceptanceInput]::GetPhysicalCursorPos([ref]$originalPointer)
    $lastPoint = $null
    try {
        # Enter each segment independently: MDY auto-advances after Month, while
        # YMD behaves differently. Never infer focus from a fixed arrow sequence.
        $targets = @{}
        foreach ($part in $dateParts) { $targets[$part.Part] = $part.Digits }
        $steps = @(@('Day', '01'), @('Year', $targets.Year), @('Month', $targets.Month), @('Day', $targets.Day))
        foreach ($step in $steps) {
            $segmentName = $step[0]
            $segment = Find-Control $dateControl $name ($segmentName + ' Jump to local date')
            $bounds = $segment.Current.BoundingRectangle
            if ($bounds.Width -le 0 -or $bounds.Height -le 0) { throw 'Date segment is not visible.' }
            $point = @{ X = [int]($bounds.Left + $bounds.Width / 2); Y = [int]($bounds.Top + $bounds.Height / 2) }
            Wait-For 'schedule-date-segment-owned' { [RigarusAcceptanceInput]::ClickOwned($point.X, $point.Y, $process.MainWindowHandle) } | Out-Null
            $lastPoint = $point
            Wait-For 'schedule-date-segment-focused' {
                ([string][Windows.Automation.AutomationElement]::FocusedElement.Current.Name).StartsWith($segmentName + ' ')
            } | Out-Null
            if ([RigarusAcceptanceInput]::GetForegroundWindow() -ne $process.MainWindowHandle) { throw 'Test window no longer owns foreground input.' }
            [Windows.Forms.SendKeys]::SendWait('{BACKSPACE}' + $step[1])
            Wait-For 'schedule-date-segment-committed' {
                $segment.GetCurrentPattern([Windows.Automation.RangeValuePattern]::Pattern).Current.Value -eq [double]$step[1]
            } | Out-Null
        }
        [Windows.Forms.SendKeys]::SendWait('{TAB}')
    }
    finally {
        $currentPointer = New-Object RigarusAcceptanceInput+Point
        $null = [RigarusAcceptanceInput]::GetPhysicalCursorPos([ref]$currentPointer)
        if ($lastPoint -and $currentPointer.X -eq $lastPoint.X -and $currentPointer.Y -eq $lastPoint.Y) {
            $null = [RigarusAcceptanceInput]::SetPhysicalCursorPos($originalPointer.X, $originalPointer.Y)
        }
    }
    Wait-For 'schedule-date-committed' { $dateControl.GetCurrentPattern($valuePattern).Current.Value -ceq $Date } | Out-Null
    Invoke-Button $Window 'Go'
    Find-Control $Window $name 'Job Schedule Sunday–Saturday' | Out-Null
}

function Get-SyntheticAssignmentCards($Window) {
    $table = Find-Control $Window $name 'Job Schedule Sunday–Saturday'
    $condition = [Windows.Automation.PropertyCondition]::new(
        [Windows.Automation.AutomationElement]::ControlTypeProperty,
        [Windows.Automation.ControlType]::Button)
    @($table.FindAll([Windows.Automation.TreeScope]::Descendants, $condition) |
        Where-Object { $_.Current.Name -match '^Draft [1-9][0-9]*, SYN-14-UI, ' })
}

function Assert-WeekAssignmentCards($Window, [string[]]$Expected) {
    $observation = @{ Values = @() }
    try { Wait-For 'weekly-synthetic-cards' {
        $observation.Values = @(Get-SyntheticAssignmentCards $Window | ForEach-Object { $_.Current.Name } | Sort-Object)
        ($observation.Values -join '|') -ceq (($Expected | Sort-Object) -join '|')
    } | Out-Null }
    catch {
        Write-AcceptanceEvent 'INFO' 'weekly-card-diagnostic' $timer 0 ("actual=$($observation.Values -join '|') expected=$($Expected -join '|')")
        throw
    }
}

function Open-WeekAssignment($Window, [int]$Id, [string]$DateSlot) {
    $label = "Draft $Id, SYN-14-UI, $DateSlot, Assignment Test Crew"
    $condition = [Windows.Automation.AndCondition]::new(
        [Windows.Automation.PropertyCondition]::new($name, $label),
        [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty, [Windows.Automation.ControlType]::Button))
    $observation = @{ State = 'not-observed' }
    # A view switch replaces source nodes; do not poll the old provider forever.
    # Scroll the current card before testing enabled state, as an operator would.
    try { Wait-For 'weekly-source-visible-and-enabled' {
        $card = $Window.FindFirst([Windows.Automation.TreeScope]::Descendants, $condition)
        if (-not $card) { return $false }
        $observation.State = "id=$Id enabled=$($card.Current.IsEnabled) offscreen=$($card.Current.IsOffscreen) bounds=$($card.Current.BoundingRectangle)"
        $scrollItem = $null
        if ($card.TryGetCurrentPattern([Windows.Automation.ScrollItemPattern]::Pattern, [ref]$scrollItem)) { $scrollItem.ScrollIntoView() }
        $card.Current.IsEnabled -and -not $card.Current.IsOffscreen
    } | Out-Null }
    catch { Write-AcceptanceEvent 'INFO' 'weekly-source-diagnostic' $timer 0 $observation.State; throw }
    Invoke-Button $Window $label
    Find-Control $Window $name ("Edit Draft $Id") -Button | Out-Null
}

function Close-AssignmentDetails($Window, [int]$Id) {
    Find-Control $Window $name ("Edit Draft $Id") -Button | Out-Null
    Invoke-Button $Window 'Close dialog'
}

function Get-SyntheticAssignmentDigest {
    # Only the private, generated smoke profile is observed; ignore transient SHM locks.
    $syntheticDatabase = Join-Path $root 'data/rigarus.db'
    if (-not (Test-Path -LiteralPath $syntheticDatabase -PathType Leaf)) { throw 'Synthetic database is missing.' }
    (@($syntheticDatabase, ($syntheticDatabase + '-wal')) | ForEach-Object {
        if (Test-Path -LiteralPath $_ -PathType Leaf) { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash }
        else { 'absent' }
    }) -join ':'
}

function Initialize-SyntheticWeeklyScale($Window) {
    foreach ($number in 2..9) {
        Invoke-Button $Window 'New crew'
        $label = 'Weekly Test Crew ' + $number.ToString('00')
        if ($number -eq 9) { $label += ' long synthetic alignment label' }
        Set-Field $Window 'crew-name' $label
        Invoke-Button $Window 'Save crew'
        Find-Control $Window $name 'Crew saved.' | Out-Null
    }
    Invoke-Button $Window 'Projects'
    Invoke-Button $Window 'Bulk Add Projects'
    $lines = @('Project Number,Site ID,Site Name')
    $lines += @(1..100 | ForEach-Object { 'SYN-WEEK-' + $_.ToString('000') + ',' + $_.ToString('0000') + ',Synthetic weekly scale site ' + $_ })
    Set-Field $Window 'bulk-text' ($lines -join "`n")
    Invoke-Button $Window 'Preview projects'
    Invoke-Button $Window 'Confirm 100 projects'
    Find-Control $Window $name 'SYN-WEEK-001' -Button | Out-Null
}

function Assert-SyntheticWeeklyScroll($Window) {
    $table = Find-Control $Window $name 'Crew Board Sunday–Saturday'
    $grid = $table.GetCurrentPattern([Windows.Automation.GridPattern]::Pattern)
    if ($grid.Current.RowCount -lt 10 -or $grid.Current.ColumnCount -ne 8) { throw 'Expected nine Crews and seven day columns.' }
    $lastRow = 0
    for ($row = 1; $row -lt $grid.Current.RowCount; $row++) {
        if ($grid.GetItem($row, 0).Current.Name.StartsWith('Weekly Test Crew 09')) { $lastRow = $row; break }
    }
    if (-not $lastRow) { throw 'The ninth synthetic Crew is missing.' }
    $region = Find-Control $Window $name 'Scrollable weekly schedule'
    $scroll = $region.GetCurrentPattern([Windows.Automation.ScrollPattern]::Pattern)
    if (-not $scroll.Current.VerticallyScrollable -or -not $scroll.Current.HorizontallyScrollable) { throw 'Expected both scroll axes in the bounded test viewport.' }
    $scroll.SetScrollPercent(100, 100)
    $observation = @{ State = 'not-observed' }
    try { Wait-For 'last-crew-sticky-header-alignment' {
        # Switching boards intentionally focuses the selected source after paint.
        # Reapply the operator scroll if that deferred focus won the first race.
        if ($scroll.Current.VerticalScrollPercent -lt 99.99 -or $scroll.Current.HorizontalScrollPercent -lt 99.99) {
            $scroll.SetScrollPercent(100, 100)
            return $false
        }
        $bounds = $region.Current.BoundingRectangle
        $roster = $grid.GetItem($lastRow, 0).Current.BoundingRectangle
        $day = $grid.GetItem($lastRow, 7).Current.BoundingRectangle
        $header = $grid.GetItem(0, 7).Current.BoundingRectangle
        $observation.State = "row=$lastRow region=$bounds roster=$roster day=$day header=$header vertical=$($scroll.Current.VerticalScrollPercent) horizontal=$($scroll.Current.HorizontalScrollPercent)"
        $roster.Width -gt 0 -and $roster.Height -gt 0 -and $day.Width -gt 0 -and
            $roster.Bottom -gt $header.Bottom -and $roster.Bottom -le ($bounds.Bottom + 2) -and
            [Math]::Abs($roster.Top - $day.Top) -le 2 -and [Math]::Abs($roster.Bottom - $day.Bottom) -le 2 -and
            [Math]::Abs($roster.Left - $bounds.Left) -le 3 -and $header.Top -ge $bounds.Top -and $header.Bottom -lt $roster.Bottom
    } | Out-Null }
    catch { Write-AcceptanceEvent 'INFO' 'weekly-scroll-diagnostic' $timer 0 $observation.State; throw }
    # A wrapped roster can legitimately exceed the body viewport. Check both ends
    # instead of inventing a maximum name/member/row height to make it fit at once.
    # UIA view percentages and the region's outer bounds do not share exact
    # border/scrollbar rounding. Reobserve after bounded small steps instead of
    # estimating one percentage that can leave the name under the sticky header.
    try { Wait-For 'last-crew-name-reachable' {
        $bounds = $region.Current.BoundingRectangle
        $roster = $grid.GetItem($lastRow, 0).Current.BoundingRectangle
        $day = $grid.GetItem($lastRow, 7).Current.BoundingRectangle
        $header = $grid.GetItem(0, 7).Current.BoundingRectangle
        $observation.State = "row=$lastRow region=$bounds roster=$roster day=$day header=$header vertical=$($scroll.Current.VerticalScrollPercent) horizontal=$($scroll.Current.HorizontalScrollPercent) viewSize=$($scroll.Current.VerticalViewSize)"
        if ($roster.Top -lt ($header.Bottom - 2)) {
            $scroll.Scroll([Windows.Automation.ScrollAmount]::NoAmount, [Windows.Automation.ScrollAmount]::SmallDecrement)
            return $false
        }
        if ($roster.Top -ge $bounds.Bottom) {
            $scroll.Scroll([Windows.Automation.ScrollAmount]::NoAmount, [Windows.Automation.ScrollAmount]::SmallIncrement)
            return $false
        }
        $roster.Top -ge ($header.Bottom - 2) -and $roster.Top -lt $bounds.Bottom -and
            [Math]::Abs($roster.Top - $day.Top) -le 2 -and [Math]::Abs($roster.Left - $bounds.Left) -le 3
    } | Out-Null }
    catch { Write-AcceptanceEvent 'INFO' 'weekly-name-scroll-diagnostic' $timer 0 $observation.State; throw }
    $scroll.SetScrollPercent(0, 0)
    Write-AcceptanceEvent 'PASS' 'weekly-scale-scroll' $timer 0 'crews=9 projectsAtLeast=101 lastCrewTopAndBottom=reachable stickyDate=visible stickyRoster=aligned method=UIA-ScrollPattern windowDips=1000x720'
}

function Test-Assignments($Window) {
    Invoke-Button $Window 'Crews'
    Invoke-Button $Window 'New crew'
    Set-Field $Window 'crew-name' 'Assignment Test Crew'
    Invoke-Button $Window 'Save crew'
    Find-Control $Window $name 'Crew saved.' | Out-Null
    Initialize-SyntheticWeeklyScale $Window
    Invoke-Button $Window 'Projects'
    Invoke-Button $Window 'New project'
    Set-Field $Window 'job_number' 'SYN-14-UI'
    Set-Field $Window 'site_id' '0014'
    Set-Field $Window 'site_name' 'Synthetic scheduling site'
    Invoke-Button $Window 'Add work item'
    Select-AssignmentChoice $Window 'type-0' 'c' 'Civil'
    Invoke-Button $Window 'Add work item'
    Select-AssignmentChoice $Window 'type-1' 't' 'Tower'
    Invoke-Button $Window 'Save project'
    $table = Find-Control $Window $name 'Project work items'
    $grid = $table.GetCurrentPattern([Windows.Automation.GridPattern]::Pattern)
    $buttonCondition = [Windows.Automation.PropertyCondition]::new(
        [Windows.Automation.AutomationElement]::ControlTypeProperty, [Windows.Automation.ControlType]::Button)
    $civilName = $grid.GetItem(1, 3).FindFirst([Windows.Automation.TreeScope]::Descendants, $buttonCondition).Current.Name
    $towerName = $grid.GetItem(2, 3).FindFirst([Windows.Automation.TreeScope]::Descendants, $buttonCondition).Current.Name
    $script:assignmentCivilId = [int]($civilName -replace '^Assign Work Item ', '')
    $script:assignmentTowerId = [int]($towerName -replace '^Assign Work Item ', '')

    foreach ($slot in @('AM', 'PM')) {
        Open-SyntheticAssignment $Window $assignmentCivilId
        Select-AssignmentChoice $Window 'assignment-crew' 'a' 'Assignment Test Crew'
        Set-Field $Window 'assignment-date' '2026-12-31'
        Select-AssignmentChoice $Window 'assignment-slot' $(if ($slot -eq 'AM') { '{HOME}' } else { '{END}' }) $slot
        Set-Field $Window 'assignment-notes' ('Synthetic visit ' + $slot)
        Invoke-Button $Window 'Save to Draft'
        Close-AssignmentDetails $Window $(if ($slot -eq 'AM') { 1 } else { 2 })
    }
    $am = 'Draft 1, SYN-14-UI, 2026-12-31 AM, Assignment Test Crew'
    $pm = 'Draft 2, SYN-14-UI, 2026-12-31 PM, Assignment Test Crew'
    $tower = 'Draft 3, SYN-14-UI, 2027-01-01 AM, Assignment Test Crew'
    $replacement = 'Draft 4, SYN-14-UI, 2026-12-31 AM, Assignment Test Crew'
    Assert-WeekAssignmentCards $Window @($am, $pm)
    Invoke-Button $Window 'Review & Publish'
    $publish = Find-Control $Window $name 'Publish schedule unavailable' -Button
    if ($publish.Current.IsEnabled) { throw 'Draft publication must remain disabled.' }
    Invoke-Button $Window 'Close dialog'
    Open-SyntheticAssignment $Window $assignmentTowerId
    Select-AssignmentChoice $Window 'assignment-crew' 'a' 'Assignment Test Crew'
    Set-Field $Window 'assignment-date' '2026-12-31'
    Set-Field $Window 'assignment-notes' 'Synthetic Tower visit'
    Invoke-Button $Window 'Save to Draft'
    Assert-SyntheticTextContains $Window 'already has Draft Assignment #1 on 2026-12-31 AM'
    if ((Find-Control $Window $automationId 'assignment-notes').GetCurrentPattern($valuePattern).Current.Value -ne 'Synthetic Tower visit') {
        throw 'Conflict discarded the unsaved assignment notes.'
    }
    Set-Field $Window 'assignment-date' '2027-01-01'
    Invoke-Button $Window 'Save to Draft'
    Close-AssignmentDetails $Window 3
    Assert-WeekAssignmentCards $Window @($am, $pm, $tower)

    $beforeCancel = Get-SyntheticAssignmentDigest
    Open-SyntheticAssignment $Window $assignmentCivilId
    Select-AssignmentChoice $Window 'assignment-crew' 'a' 'Assignment Test Crew'
    Set-Field $Window 'assignment-date' '2027-01-02'
    Set-Field $Window 'assignment-notes' 'Synthetic unsaved cancelled form'
    Invoke-Button $Window 'Cancel'
    if ((Get-SyntheticAssignmentDigest) -cne $beforeCancel) { throw 'Form cancellation modified the synthetic SQLite database/WAL.' }
    Show-SyntheticAssignmentDate $Window '2026-12-31'
    Assert-WeekAssignmentCards $Window @($am, $pm, $tower)
    Open-WeekAssignment $Window 2 '2026-12-31 PM'
    Invoke-Button $Window 'Edit Draft 2'
    Set-Field $Window 'assignment-notes' 'Edited synthetic PM visit'
    Invoke-Button $Window 'Save to Draft'
    Assert-SyntheticTextContains $Window 'Edited synthetic PM visit'
    Close-AssignmentDetails $Window 2
    Open-WeekAssignment $Window 1 '2026-12-31 AM'
    Invoke-Button $Window 'Cancel Draft 1'
    Invoke-Button $Window 'Keep draft'
    Invoke-Button $Window 'Cancel Draft 1'
    Invoke-Button $Window 'Confirm cancellation'
    Assert-WeekAssignmentCards $Window @($pm, $tower)
    Assert-SyntheticTextContains $Window 'Draft cancelled. Its slot is available'
    Open-SyntheticAssignment $Window $assignmentCivilId
    Select-AssignmentChoice $Window 'assignment-crew' 'a' 'Assignment Test Crew'
    Set-Field $Window 'assignment-date' '2026-12-31'
    Invoke-Button $Window 'Save to Draft'
    Close-AssignmentDetails $Window 4
    Assert-WeekAssignmentCards $Window @($replacement, $pm, $tower)
    Invoke-Button $Window 'Crew Board'
    Find-Control $Window $name 'Crew Board Sunday–Saturday' | Out-Null
    Find-Control $Window $name $replacement -Button | Out-Null
    Find-Control $Window $name $pm -Button | Out-Null
    Find-Control $Window $name $tower -Button | Out-Null
    Assert-SyntheticTextContains $Window 'Time off not configured'
    Assert-SyntheticWeeklyScroll $Window
    Invoke-Button $Window 'Job Schedule'
    Show-SyntheticAssignmentDate $Window '2027-01-03'
    Assert-WeekAssignmentCards $Window @()
    Find-Control $Window $name 'No assignments in this view for the selected week.' | Out-Null
    Invoke-Button $Window 'Previous week'
    Assert-WeekAssignmentCards $Window @($replacement, $pm, $tower)
    Write-AcceptanceEvent 'PASS' 'assignment-lifecycle' $timer 0 'weeklyBoards=shared civilAndTower=independent amPm=saved collision=rejected formCancel=dbAndWalUnchanged edit=retained savedCancel=hidden freedSlot=reused emptyWeek=verified publish=disabled'
}

function Test-AssignmentsReopened($Window) {
    Invoke-Button $Window 'Schedule'
    Invoke-Button $Window 'Job Schedule'
    Show-SyntheticAssignmentDate $Window '2026-12-31'
    Assert-WeekAssignmentCards $Window @(
        'Draft 4, SYN-14-UI, 2026-12-31 AM, Assignment Test Crew',
        'Draft 2, SYN-14-UI, 2026-12-31 PM, Assignment Test Crew',
        'Draft 3, SYN-14-UI, 2027-01-01 AM, Assignment Test Crew')
    Open-WeekAssignment $Window 2 '2026-12-31 PM'
    Assert-SyntheticTextContains $Window 'Edited synthetic PM visit'
    Invoke-Button $Window 'Edit Draft 2'
    Wait-For 'civil-work-item-id-reopened' {
        $choice = Find-Control $Window $automationId 'assignment-work-item'
        ([string]$choice.GetCurrentPattern($valuePattern).Current.Value).StartsWith("Civil $([char]0x00B7) Work Item #$assignmentCivilId $([char]0x00B7)")
    } | Out-Null
    Invoke-Button $Window 'Cancel'
    Close-AssignmentDetails $Window 2
    Open-WeekAssignment $Window 3 '2027-01-01 AM'
    Assert-SyntheticTextContains $Window 'Synthetic Tower visit'
    Invoke-Button $Window 'Edit Draft 3'
    Wait-For 'tower-work-item-id-reopened' {
        $choice = Find-Control $Window $automationId 'assignment-work-item'
        ([string]$choice.GetCurrentPattern($valuePattern).Current.Value).StartsWith("Tower $([char]0x00B7) Work Item #$assignmentTowerId $([char]0x00B7)")
    } | Out-Null
    Invoke-Button $Window 'Cancel'
    Close-AssignmentDetails $Window 3
    Write-AcceptanceEvent 'PASS' 'assignment-reopen' $timer 0 'threeDraftVisits=preserved notes=preserved workItemIds=preserved crossYearDates=preserved cancelledCard=absent'
}

function Open-SyntheticWorkingCalendar($Window, [string]$Scope, [string]$Owner) {
    Invoke-Button $Window 'Schedule'
    Invoke-Button $Window 'Working calendars'
    Select-AssignmentChoice $Window 'working-scope' '' $Scope
    if ($Scope -eq 'Project') {
        # Large native select popups expose disabled DOM proxies rather than
        # selectable option providers under this WebView2 UIA tree. Exercise the
        # normal keyboard path only after verifying our owned foreground/focus.
        $control = Find-Control $Window $automationId 'working-owner'
        $control.SetFocus()
        Get-UiaElementSnapshot $Window | Out-Null
        Wait-For 'working-owner-keyboard-focus' {
            $focused = [Windows.Automation.AutomationElement]::FocusedElement
            $control.Current.IsEnabled -and $focused.Current.AutomationId -eq 'working-owner' -and
                [RigarusUiaWindowState]::GetForegroundWindow() -eq $script:uiaOwnedHandle
        } | Out-Null
        Add-Type -AssemblyName System.Windows.Forms
        [Windows.Forms.SendKeys]::SendWait('SYN-14-UI{ENTER}')
        Wait-For 'working-project-choice-verified' {
            $live = Find-Control $Window $automationId 'working-owner'
            $observed = [string]$live.GetCurrentPattern($valuePattern).Current.Value
            Test-UiaChoiceLabel $observed $Owner
        } | Out-Null
    }
    else { Select-AssignmentChoice $Window 'working-owner' '' $Owner }
    Set-Field $Window 'working-date' '2026-12-31'
    Invoke-Button $Window 'Go to date'
}

function Test-WorkingCalendars($Window) {
    $projectLabel = 'SYN-14-UI ' + [char]0x00B7 + ' Synthetic scheduling site'
    Open-SyntheticWorkingCalendar $Window 'Project' $projectLabel
    Find-Control $Window $name '2026-12-31 AM: Not recorded' -Button | Out-Null
    Invoke-Button $Window 'Record working dates'
    Set-Field $Window 'working-start' '2026-12-31'
    Set-Field $Window 'working-end' '2027-01-01'
    Invoke-Button $Window 'Save working dates'
    Find-Control $Window $name '2027-01-01 PM: Can work' -Button | Out-Null
    Invoke-Button $Window '2026-12-31 AM: Can work'
    Select-AssignmentChoice $Window 'working-state' '' 'Cannot work'
    Invoke-Button $Window 'Save working dates'
    Find-Control $Window $name '2026-12-31 AM: Cannot work' -Button | Out-Null
    Find-Control $Window $name '2026-12-31 PM: Can work' -Button | Out-Null
    Invoke-Button $Window '2026-12-31 PM: Can work'
    Select-AssignmentChoice $Window 'working-state' '' 'Not recorded (clear)'
    $before = Get-SyntheticAssignmentDigest
    Invoke-Button $Window 'Cancel'
    $after = Get-SyntheticAssignmentDigest
    if ($before -ne $after) { throw 'Working-calendar Cancel changed SQLite/WAL.' }
    Invoke-Button $Window '2026-12-31 PM: Can work'
    Select-AssignmentChoice $Window 'working-state' '' 'Not recorded (clear)'
    Invoke-Button $Window 'Save working dates'
    Find-Control $Window $name '2026-12-31 PM: Not recorded' -Button | Out-Null
    Invoke-Button $Window 'Calendar change history'
    Assert-SyntheticTextContains $Window 'Revision 3:'
    Invoke-Button $Window 'Close dialog'
    Open-SyntheticWorkingCalendar $Window 'Crew' 'Assignment Test Crew'
    Invoke-Button $Window 'Record working dates'
    Set-Field $Window 'working-start' '2026-12-31'
    Set-Field $Window 'working-end' '2027-01-01'
    Invoke-Button $Window 'Save working dates'
    Find-Control $Window $name '2027-01-01 PM: Can work' -Button | Out-Null
    Invoke-Button $Window 'Job Schedule'
    Show-SyntheticAssignmentDate $Window '2026-12-31'
    Open-WeekAssignment $Window 4 '2026-12-31 AM'
    Assert-SyntheticTextContains $Window 'Calendar conflict:'
    Close-AssignmentDetails $Window 4
    Open-WeekAssignment $Window 2 '2026-12-31 PM'
    Assert-SyntheticTextContains $Window 'Calendar pending:'
    Invoke-Button $Window 'Edit Draft 2'
    Assert-SyntheticTextContains $Window 'Calendar pending:'
    Invoke-Button $Window 'Save to Draft'
    Close-AssignmentDetails $Window 2
    Open-WeekAssignment $Window 3 '2027-01-01 AM'
    Assert-SyntheticTextContains $Window 'Calendar matched:'
    Close-AssignmentDetails $Window 3
    Write-AcceptanceEvent 'PASS' 'working-calendars' $timer 0 'projectShared=true crewIndependent=true AMPM=isolated cancel=noWrite draft=advisory'
}

function Test-WorkingCalendarsReopened($Window) {
    $projectLabel = 'SYN-14-UI ' + [char]0x00B7 + ' Synthetic scheduling site'
    Open-SyntheticWorkingCalendar $Window 'Project' $projectLabel
    Find-Control $Window $name '2026-12-31 AM: Cannot work' -Button | Out-Null
    Find-Control $Window $name '2026-12-31 PM: Not recorded' -Button | Out-Null
    Find-Control $Window $name '2027-01-01 AM: Can work' -Button | Out-Null
    Invoke-Button $Window 'Calendar change history'
    Assert-SyntheticTextContains $Window 'Revision 3:'
    Invoke-Button $Window 'Close dialog'
    Write-AcceptanceEvent 'PASS' 'working-calendar-reopen' $timer 0 'projectCalendar=preserved sparseClear=preserved history=preserved'
}

function Initialize-SyntheticStaffingPeople($Window) {
    Invoke-Button $Window 'Crews'
    Invoke-Button $Window 'New crew'
    Set-Field $Window 'crew-name' 'Synthetic Tower Home'
    Select-AssignmentChoice $Window 'crew-type' '' 'Tower'
    Invoke-Button $Window 'Save crew'
    Find-Control $Window $name 'Crew saved.' | Out-Null
    foreach ($person in @('Synthetic Staffing A', 'Synthetic Staffing B')) {
        Invoke-Button $Window 'Employees'
        Invoke-Button $Window 'New employee'
        Set-Field $Window 'employee-name' $person
        Select-AssignmentChoice $Window 'employee-home-crew' '' 'Synthetic Tower Home (Tower #2)'
        if ($person -eq 'Synthetic Staffing B') { Select-AssignmentChoice $Window 'employee-active' '' 'Inactive' }
        Select-AssignmentChoice $Window 'employee-skill' '' '1'
        Invoke-Button $Window 'Save employee'
        Find-Control $Window $name 'Employee saved.' | Out-Null
    }
}

function Assert-AvailabilityCell($Window, [string]$Date, [string]$Slot, [string]$State) {
    Wait-For 'availability-cell-state' {
        $cell = Find-Control $Window $automationId "availability-cell-$Date-$Slot"
        $cell.Current.Name -ceq "$Date ${Slot}: $State"
    } | Out-Null
}

function Open-SyntheticAvailability($Window) {
    Invoke-Button $Window 'People'
    Invoke-Button $Window 'Availability'
    Find-Control $Window $automationId 'availability-date' | Out-Null
    Set-Field $Window 'availability-date' '2026-12-31'
    Invoke-Button $Window 'Go to availability date'
}

function Test-Availability($Window) {
    Open-SyntheticAvailability $Window
    Assert-AvailabilityCell $Window '2026-12-31' 'AM' 'Not recorded'
    Invoke-Button $Window 'Record availability'
    Set-Field $Window 'availability-start' '2026-12-31'
    Set-Field $Window 'availability-end' '2027-01-01'
    Invoke-Button $Window 'Save availability'
    Assert-AvailabilityCell $Window '2026-12-31' 'AM' 'Available'
    Assert-AvailabilityCell $Window '2026-12-31' 'PM' 'Available'
    Assert-AvailabilityCell $Window '2027-01-01' 'AM' 'Available'
    Assert-AvailabilityCell $Window '2027-01-01' 'PM' 'Available'
    Invoke-Button $Window '2026-12-31 AM: Available'
    Select-AssignmentChoice $Window 'availability-state' '' 'Unavailable'
    Invoke-Button $Window 'Save availability'
    Assert-AvailabilityCell $Window '2026-12-31' 'AM' 'Unavailable'
    Invoke-Button $Window '2026-12-31 PM: Available'
    Select-AssignmentChoice $Window 'availability-state' '' 'Not recorded'
    $before = Get-SyntheticAssignmentDigest
    Invoke-Button $Window 'Cancel availability changes'
    if ((Get-SyntheticAssignmentDigest) -cne $before) { throw 'Availability Cancel modified synthetic SQLite/WAL.' }
    Assert-AvailabilityCell $Window '2026-12-31' 'PM' 'Available'
    Invoke-Button $Window '2026-12-31 PM: Available'
    Select-AssignmentChoice $Window 'availability-state' '' 'Not recorded'
    Invoke-Button $Window 'Save availability'
    Assert-AvailabilityCell $Window '2026-12-31' 'PM' 'Not recorded'
    Assert-AvailabilityCell $Window '2026-12-31' 'AM' 'Unavailable'
    Select-AssignmentChoice $Window 'availability-employee' '' "$staffingWorkerBName (#2)"
    Assert-AvailabilityCell $Window '2026-12-31' 'AM' 'Not recorded'
    Assert-AvailabilityCell $Window '2027-01-01' 'AM' 'Not recorded'
    Select-AssignmentChoice $Window 'availability-employee' '' "$staffingWorkerAName (#1)"
    Assert-AvailabilityCell $Window '2026-12-31' 'AM' 'Unavailable'
    Invoke-Button $Window 'Schedule'
    Invoke-Button $Window 'Job Schedule'
    Show-SyntheticAssignmentDate $Window '2026-12-31'
    Write-AcceptanceEvent 'PASS' 'availability-lifecycle' $timer 0 'fullDay=inclusive crossYear=retained amPm=independent clear=historyRetained cancel=dbAndWalUnchanged employeeSwitch=isolated'
}

function Test-AvailabilityReopened($Window) {
    Open-SyntheticAvailability $Window
    Assert-AvailabilityCell $Window '2026-12-31' 'AM' 'Unavailable'
    Assert-AvailabilityCell $Window '2026-12-31' 'PM' 'Not recorded'
    Assert-AvailabilityCell $Window '2027-01-01' 'AM' 'Available'
    Assert-AvailabilityCell $Window '2027-01-01' 'PM' 'Available'
    Write-AcceptanceEvent 'PASS' 'availability-reopen' $timer 0 'threeStates=preserved explicitRange=preserved existingHomeCrewAndDraft=unchanged'
}

function Test-EmployeeWeek($Window) {
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $employeeWeekBefore = Get-SyntheticAssignmentDigest
    Invoke-Button $Window 'Schedule'
    Invoke-Button $Window 'Job Schedule'
    Show-SyntheticAssignmentDate $Window '2026-12-31'
    Invoke-Button $Window 'Employee Week'
    Select-AssignmentChoice $Window 'employee-week-person' '' "$staffingWorkerAName (#1)"
    Find-Control $Window $automationId 'employee-visit-4' -Button | Out-Null
    Assert-SyntheticTextContains $Window 'AM: Unavailable'
    Invoke-Button $Window 'Export preview'
    Find-Control $Window $name 'DRAFT – NOT CONFIRMED' | Out-Null
    foreach ($label in @('Export PDF','Export Excel')) {
        $button = Find-Control $Window $name $label -Button
        if ($button.Current.IsEnabled) { throw 'Formal employee export unexpectedly enabled.' }
    }
    Invoke-Button $Window 'Close preview'
    Select-AssignmentChoice $Window 'employee-week-person' '' "$staffingWorkerBName (#2)"
    Find-Control $Window $name 'No actual assignments for this employee this week.' | Out-Null
    $visitCondition = [Windows.Automation.PropertyCondition]::new($automationId, 'employee-visit-4')
    if ($Window.FindAll([Windows.Automation.TreeScope]::Descendants,$visitCondition).Count) { throw 'Previous employee visit remained visible.' }
    Invoke-Button $Window 'People'
    Invoke-Button $Window ('Open employee week for ' + $staffingWorkerAName)
    Find-Control $Window $automationId 'employee-visit-4' -Button | Out-Null
    Invoke-Button $Window 'Job Schedule'
    if ((Get-SyntheticAssignmentDigest) -cne $employeeWeekBefore) { throw 'Read-only employee week changed synthetic SQLite/WAL.' }
    Write-AcceptanceEvent 'PASS' 'employee-week' $timer 0 'explicitWorker=shown borrowedCrew=retained emptyEmployee=clear availability=recorded preview=draft export=disabled handoff=week-retained'
}

function Set-SyntheticWorker($Window, [string]$Label, [bool]$Selected) {
    $control = Find-Control $Window $name $Label
    $toggle = $control.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern)
    $wanted = if ($Selected) { [Windows.Automation.ToggleState]::On } else { [Windows.Automation.ToggleState]::Off }
    if ($toggle.Current.ToggleState -ne $wanted) { $toggle.Toggle() }
    Wait-For 'worker-checkbox-state' { $toggle.Current.ToggleState -eq $wanted } | Out-Null
}

function Test-Staffing($Window) {
    Show-SyntheticAssignmentDate $Window '2026-12-31'
    Open-WeekAssignment $Window 4 '2026-12-31 AM'
    Invoke-Button $Window 'Choose workers'
    Set-SyntheticWorker $Window "Select worker 1, $staffingWorkerAName" $true
    if ($IncludeAvailability) { Assert-SyntheticTextContains $Window 'Availability: Unavailable' }
    Set-SyntheticWorker $Window "Select worker 2, $staffingWorkerBName" $true
    $before = Get-SyntheticAssignmentDigest
    Invoke-Button $Window 'Cancel worker changes'
    if ((Get-SyntheticAssignmentDigest) -cne $before) { throw 'Worker form Cancel modified the synthetic SQLite database/WAL.' }
    Invoke-Button $Window 'Choose workers'
    Set-SyntheticWorker $Window "Select worker 1, $staffingWorkerAName" $true
    Invoke-Button $Window 'Save workers to Draft'
    Find-Control $Window $name 'Choose workers' -Button | Out-Null
    Assert-SyntheticTextContains $Window "$staffingWorkerAName (borrowed)"
    Close-AssignmentDetails $Window 4
    Invoke-Button $Window 'Crew Board'
    Open-WeekAssignment $Window 4 '2026-12-31 AM'
    Assert-SyntheticTextContains $Window "$staffingWorkerAName (borrowed)"
    Close-AssignmentDetails $Window 4
    Open-WeekAssignment $Window 2 '2026-12-31 PM'
    Invoke-Button $Window 'Choose workers'
    $worker = Find-Control $Window $name "Select worker 1, $staffingWorkerAName"
    if ($worker.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Current.ToggleState -ne [Windows.Automation.ToggleState]::Off) { throw 'AM staffing leaked into PM.' }
    Invoke-Button $Window 'Cancel worker changes'
    Close-AssignmentDetails $Window 2
    Write-AcceptanceEvent 'PASS' 'staffing-lifecycle' $timer 0 'explicitWorker=saved borrowed=labelled homeRoster=separate amPm=independent cancel=dbAndWalUnchanged'
}

function Test-StaffingReopened($Window) {
    Show-SyntheticAssignmentDate $Window '2026-12-31'
    Open-WeekAssignment $Window 4 '2026-12-31 AM'
    Assert-SyntheticTextContains $Window "$staffingWorkerAName (borrowed)"
    Invoke-Button $Window 'Choose workers'
    foreach ($check in @(@("Select worker 1, $staffingWorkerAName", [Windows.Automation.ToggleState]::On), @("Select worker 2, $staffingWorkerBName", [Windows.Automation.ToggleState]::Off))) {
        $worker = Find-Control $Window $name $check[0]
        if ($worker.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Current.ToggleState -ne $check[1]) { throw 'Explicit worker IDs were not retained after restart.' }
    }
    Invoke-Button $Window 'Cancel worker changes'
    Close-AssignmentDetails $Window 4
    Invoke-Button $Window 'Employees'
    Assert-TableColumn $Window 'Employee records' 1 @('Synthetic Tower Home (Tower #2)', 'Synthetic Tower Home (Tower #2)')
    Assert-TableColumn $Window 'Employee records' 4 @('Unverified', 'Unverified')
    Write-AcceptanceEvent 'PASS' 'staffing-reopen' $timer 0 'explicitWorkerIds=retained homeCrew=unchanged driver=Unverified'
}

function Set-MultiDayNotes($Window, [string]$Value) {
    $control = Find-Control $Window $automationId 'assignment-notes'
    $pattern = $control.GetCurrentPattern($valuePattern)
    $observed = @{ Matches = 0 }
    # Wait for two committed native values before Save. A single SetValue can
    # report before WebView2 finishes committing its last text-input event.
    Wait-For 'multiday-notes-committed' {
        if (([string]$pattern.Current.Value) -cne $Value) {
            $observed.Matches = 0
            $pattern.SetValue($Value)
            return $false
        }
        $observed.Matches++
        $observed.Matches -ge 2
    } | Out-Null
}

function Assert-MultiDayStrip($Window, [bool]$Expected) {
    $condition = [Windows.Automation.PropertyCondition]::new($automationId, 'assignment-span-5')
    Wait-For 'multiday-strip-state' {
        $matches = $Window.FindAll([Windows.Automation.TreeScope]::Descendants, $condition)
        if ($Expected) { $matches.Count -eq 1 } else { $matches.Count -eq 0 }
    } | Out-Null
    if ($Expected) {
        $strip = Find-Control $Window $automationId 'assignment-span-5'
        $table = Find-Control $Window $name 'Job Schedule Sunday–Saturday'
        $grid = $table.GetCurrentPattern([Windows.Automation.GridPattern]::Pattern)
        $header = $grid.GetItem(0, 6).Current.BoundingRectangle
        $bounds = $strip.Current.BoundingRectangle
        if ($bounds.Width -lt $header.Width * 1.5) { throw 'Consecutive visits did not span both date columns.' }
    }
}

function Test-MultiDayAssignments($Window) {
    # Explicit four saved visits, not an inferred duration. Original #35 fixture
    # IDs 1–4 and its selected-week assertions remain unchanged.
    $nextId = 5
    foreach ($date in @('2027-12-31', '2028-01-01')) {
        foreach ($slot in @('AM', 'PM')) {
            Open-SyntheticAssignment $Window $assignmentCivilId
            Select-AssignmentChoice $Window 'assignment-crew' 'a' 'Assignment Test Crew'
            Set-Field $Window 'assignment-date' $date
            Select-AssignmentChoice $Window 'assignment-slot' $(if ($slot -eq 'AM') { '{HOME}' } else { '{END}' }) $slot
            Set-MultiDayNotes $Window 'Synthetic consecutive full-day visits'
            Invoke-Button $Window 'Save to Draft'
            Close-AssignmentDetails $Window $nextId
            $nextId++
        }
    }
    $am = 'Draft 5, SYN-14-UI, 2027-12-31 AM, Assignment Test Crew'
    $pm = 'Draft 6, SYN-14-UI, 2027-12-31 PM, Assignment Test Crew'
    $nextAm = 'Draft 7, SYN-14-UI, 2028-01-01 AM, Assignment Test Crew'
    $nextPm = 'Draft 8, SYN-14-UI, 2028-01-01 PM, Assignment Test Crew'
    Assert-WeekAssignmentCards $Window @($am, $pm, $nextAm, $nextPm)
    Assert-MultiDayStrip $Window $true
    Invoke-Button $Window 'Crew Board'
    Find-Control $Window $automationId 'assignment-span-5' | Out-Null
    foreach ($label in @($am, $pm, $nextAm, $nextPm)) { Find-Control $Window $name $label -Button | Out-Null }
    Assert-SyntheticWeeklyScroll $Window
    Invoke-Button $Window 'Job Schedule'
    Open-WeekAssignment $Window 5 '2027-12-31 AM'
    Invoke-Button $Window 'Edit Draft 5'
    Set-MultiDayNotes $Window 'Synthetic note on only one visit'
    Invoke-Button $Window 'Save to Draft'
    Close-AssignmentDetails $Window 5
    Assert-MultiDayStrip $Window $false
    Assert-WeekAssignmentCards $Window @($am, $pm, $nextAm, $nextPm)
    Open-WeekAssignment $Window 5 '2027-12-31 AM'
    Invoke-Button $Window 'Edit Draft 5'
    Set-MultiDayNotes $Window 'Synthetic consecutive full-day visits'
    Invoke-Button $Window 'Save to Draft'
    Close-AssignmentDetails $Window 5
    Assert-MultiDayStrip $Window $true
    Open-WeekAssignment $Window 6 '2027-12-31 PM'
    Invoke-Button $Window 'Cancel Draft 6'
    Invoke-Button $Window 'Confirm cancellation'
    Assert-MultiDayStrip $Window $false
    Assert-WeekAssignmentCards $Window @($am, $nextAm, $nextPm)
    Open-SyntheticAssignment $Window $assignmentCivilId
    Select-AssignmentChoice $Window 'assignment-crew' 'a' 'Assignment Test Crew'
    Set-Field $Window 'assignment-date' '2027-12-31'
    Select-AssignmentChoice $Window 'assignment-slot' '{END}' 'PM'
    Set-MultiDayNotes $Window 'Synthetic consecutive full-day visits'
    Invoke-Button $Window 'Save to Draft'
    Close-AssignmentDetails $Window 9
    Assert-MultiDayStrip $Window $true
    Assert-WeekAssignmentCards $Window @($am, 'Draft 9, SYN-14-UI, 2027-12-31 PM, Assignment Test Crew', $nextAm, $nextPm)
    Write-AcceptanceEvent 'PASS' 'multiday-lifecycle' $timer 0 'crossYearWeekend=spanned sourceIds=independent bothBoards=shared edit=splits cancel=splits replacement=reforms publish=unchanged'
}

function Test-MultiDayReopened($Window) {
    Invoke-Button $Window 'Schedule'
    Invoke-Button $Window 'Job Schedule'
    Show-SyntheticAssignmentDate $Window '2027-12-31'
    Assert-MultiDayStrip $Window $true
    Assert-WeekAssignmentCards $Window @(
        'Draft 5, SYN-14-UI, 2027-12-31 AM, Assignment Test Crew',
        'Draft 9, SYN-14-UI, 2027-12-31 PM, Assignment Test Crew',
        'Draft 7, SYN-14-UI, 2028-01-01 AM, Assignment Test Crew',
        'Draft 8, SYN-14-UI, 2028-01-01 PM, Assignment Test Crew')
    Open-WeekAssignment $Window 5 '2027-12-31 AM'
    Assert-SyntheticTextContains $Window 'Synthetic consecutive full-day visits'
    Invoke-Button $Window 'Edit Draft 5'
    Wait-For 'multiday-work-item-id-reopened' {
        $choice = Find-Control $Window $automationId 'assignment-work-item'
        ([string]$choice.GetCurrentPattern($valuePattern).Current.Value).StartsWith("Civil $([char]0x00B7) Work Item #$assignmentCivilId $([char]0x00B7)")
    } | Out-Null
    Invoke-Button $Window 'Cancel'
    Close-AssignmentDetails $Window 5
    Write-AcceptanceEvent 'PASS' 'multiday-reopen' $timer 0 'strip=restored stableWorkItemId=retained cancelledSource=absent replacementId=retained notes=retained'
}

function Assert-NoValidationSummary($Window) {
    Wait-For 'validation-summary-cleared' {
        $condition = [Windows.Automation.PropertyCondition]::new($automationId, 'project-error-summary')
        $Window.FindAll([Windows.Automation.TreeScope]::Descendants, $condition).Count -eq 0
    } | Out-Null
}

function Test-ProjectValidation($Window) {
    Add-Type -AssemblyName System.Windows.Forms
    Invoke-Button $Window 'Projects'
    Invoke-Button $Window 'New project'
    Invoke-Button $Window 'Save project'
    Assert-InputFocus $Window 'job_number'
    Find-Control $Window $name 'Check 3 fields before saving' | Out-Null
    Set-Field $Window 'job_number' 'UX-65-NEW'
    Set-Field $Window 'site_id' 'A-7'
    Set-Field $Window 'site_name' 'Synthetic validation yard'
    Invoke-Button $Window 'Add work item'
    Set-Field $Window 'crews-0' '0'
    Set-Field $Window 'half-days-0' '1.5'
    Invoke-Button $Window 'Save project'
    Assert-InputFocus $Window 'crews-0'
    Invoke-Button $Window 'Go to Work item 1 Estimated half-days'
    Assert-InputFocus $Window 'half-days-0'
    Set-Field $Window 'crews-0' '2'
    Set-Field $Window 'half-days-0' '4'
    Assert-NoValidationSummary $Window

    foreach ($help in @(
        @{ Label = 'Job #'; Id = 'job_number' },
        @{ Label = 'Site ID'; Id = 'site_id' },
        @{ Label = 'Site name'; Id = 'site_name' },
        @{ Label = 'Type for work item 1'; Id = 'type-0' },
        @{ Label = 'Required crews for work item 1'; Id = 'crews-0' },
        @{ Label = 'Estimated half-days for work item 1'; Id = 'half-days-0' }
    )) {
        $trigger = Find-Control $Window $name ('Help: ' + $help.Label) -Button
        $trigger.SetFocus()
        Wait-For 'field-help-trigger-focused' { $trigger.Current.HasKeyboardFocus } | Out-Null
        [Windows.Forms.SendKeys]::SendWait('{ENTER}')
        $popover = Find-Control $Window $automationId ($help.Id + '-help')
        # A slow WebView2 may expose the popover before its focus transition settles.
        # Confirm keyboard focus inside this specific open popover before Escape.
        $close = Find-Control $popover $name 'Close help' -Button
        $close.SetFocus()
        Wait-For 'field-help-content-focused' { $close.Current.HasKeyboardFocus } | Out-Null
        [Windows.Forms.SendKeys]::SendWait('{ESC}')
        Wait-For 'field-help-escape-dismissed' {
            $condition = [Windows.Automation.PropertyCondition]::new($automationId, ($help.Id + '-help'))
            $Window.FindAll([Windows.Automation.TreeScope]::Descendants, $condition).Count -eq 0
        } | Out-Null
    }
    (Find-Control $Window $automationId 'job_number').SetFocus()
    [Windows.Forms.SendKeys]::SendWait('{TAB}')
    Wait-For 'tab-reaches-site-help' { (Find-Control $Window $name 'Help: Site ID' -Button).Current.HasKeyboardFocus } | Out-Null
    [Windows.Forms.SendKeys]::SendWait('{TAB}')
    Assert-InputFocus $Window 'site_id'
    [Windows.Forms.SendKeys]::SendWait('+{TAB}')
    Wait-For 'shift-tab-reaches-site-help' { (Find-Control $Window $name 'Help: Site ID' -Button).Current.HasKeyboardFocus } | Out-Null

    Invoke-Button $Window 'Add work item'
    Set-Field $Window 'crews-1' '-1'
    Invoke-Button $Window 'Save project'
    Assert-InputFocus $Window 'crews-1'
    Invoke-Button $Window 'Remove draft work item 2'
    Assert-NoValidationSummary $Window
    for ($row = 0; $row -lt 5; $row++) { Invoke-Button $Window 'Add work item' }
    Set-Field $Window 'crews-0' '0'
    Invoke-Button $Window 'Save project'
    Assert-InputFocus $Window 'crews-0'
    Invoke-Button $Window 'Cancel'
    Set-Field $Window 'project-search' 'UX-65-NEW'
    Invoke-Button $Window 'Search'
    Find-Control $Window $name 'No projects match your search.' | Out-Null

    Invoke-Button $Window 'New project'
    Set-Field $Window 'job_number' 'UX-65-NEW'
    Set-Field $Window 'site_id' 'A-7'
    Set-Field $Window 'site_name' 'Synthetic validation yard'
    Invoke-Button $Window 'Add work item'
    Set-Field $Window 'crews-0' '2'
    Set-Field $Window 'half-days-0' '4'
    Invoke-Button $Window 'Add work item'
    Set-Field $Window 'crews-1' '3'
    Set-Field $Window 'half-days-1' '6'
    Invoke-Button $Window 'Save project'
    Find-Control $Window $name 'UX-65-NEW' -Button | Out-Null
    Invoke-Button $Window 'Edit project'
    Set-Field $Window 'crews-1' '0'
    Invoke-Button $Window 'Save project'
    Assert-InputFocus $Window 'crews-1'
    Set-Field $Window 'crews-1' '3'
    Invoke-Button $Window 'Save project'
    Find-Control $Window $name 'UX-65-NEW' -Button | Out-Null
    Write-AcceptanceEvent 'PASS' 'project-validation' $timer 0 'fields=targeted summary=focusable validCounts=accepted help=allSix keyboard=verified removedDraft=cleared cancel=readonly'
}

function Assert-TableColumn($Window, [string]$TableName, [int]$Column, [string[]]$Expected) {
    $table = Find-Control $Window $name $TableName
    $observation = @{ Rows = -1; Values = @() }
    try { Wait-For 'synthetic-table-row-order' {
        $grid = $table.GetCurrentPattern([Windows.Automation.GridPattern]::Pattern)
        $observation.Rows = $grid.Current.RowCount
        if ($grid.Current.RowCount -ne $Expected.Count + 1) { return $false }
        $values = for ($row = 1; $row -lt $grid.Current.RowCount; $row++) {
            $grid.GetItem($row, $Column).Current.Name
        }
        $observation.Values = @($values)
        ($values -join '|') -ceq ($Expected -join '|')
    } | Out-Null }
    catch {
        # This harness creates synthetic fixtures only; record the observed cells for reproduction.
        Write-AcceptanceEvent 'INFO' 'synthetic-table-diagnostic' $timer 0 ("rows=$($observation.Rows) expectedRows=$($Expected.Count + 1) actual=$($observation.Values -join '|') expected=$($Expected -join '|')")
        throw
    }
}

function Test-BulkProjects($Window) {
    Invoke-Button $Window 'Projects'
    Invoke-Button $Window 'Bulk Add Projects'
    Add-Type -AssemblyName System.Windows.Forms
    $previousClipboard = [Windows.Forms.Clipboard]::GetDataObject()
    try {
        foreach ($format in @('TSV', 'CSV')) {
            $delimiter = if ($format -eq 'TSV') { "`t" } else { ',' }
            $expected = @(
                "Project Number${delimiter}Site ID${delimiter}Site Name",
                "VM-0001${delimiter}0001${delimiter}Synthetic VM Yard A",
                "VM-0002${delimiter}0002${delimiter}Synthetic VM Yard B",
                "VM-0003${delimiter}0003${delimiter}North Field Pad 1"
            ) -join "`n"
            $expected += "`n"
            Invoke-Button $Window "Copy $format example"
            Wait-For 'example-copied-exact-delimiters' {
                ([Windows.Forms.Clipboard]::GetText() -replace "`r`n", "`n") -ceq $expected
            } | Out-Null
            Set-Field $Window 'bulk-text' ([Windows.Forms.Clipboard]::GetText())
            Invoke-Button $Window 'Preview projects'
            Find-Control $Window $name 'Confirm 3 projects' -Button | Out-Null
        }
    }
    finally {
        if ($previousClipboard) { [Windows.Forms.Clipboard]::SetDataObject($previousClipboard, $true) }
        else { [Windows.Forms.Clipboard]::Clear() }
    }
    Invoke-Button $Window 'Help: Accepted formats'
    Find-Control $Window $automationId 'bulk-help-formats' | Out-Null
    $helpButton = Find-Control $Window $name 'Help: Accepted formats' -Button
    $helpButton.SetFocus()
    [Windows.Forms.SendKeys]::SendWait('{ESC}')
    Wait-For 'help-dismissed-with-escape' {
        $condition = [Windows.Automation.PropertyCondition]::new($automationId, 'bulk-help-formats')
        $Window.FindAll([Windows.Automation.TreeScope]::Descendants, $condition).Count -eq 0
    } | Out-Null
    $content = "Project Number,Site ID,Site Name`nSYN-BULK-0002,0002,Synthetic bulk yard`ndemo-26001,9999,Do not overwrite`nSYN-BULK-DUP,03,Repeat A`nsyn-bulk-dup,04,Repeat B`nSYN-BULK-BAD,,Missing ID`n"
    Set-Field $Window 'bulk-text' $content
    Invoke-Button $Window 'Preview projects'
    Find-Control $Window $name 'Confirm 1 project' -Button | Out-Null
    # Editing invalidates the visible confirmation, even if only whitespace changes.
    Set-Field $Window 'bulk-text' ($content + "`n")
    Wait-For 'bulk-edited-preview-invalidated' {
        $condition = [Windows.Automation.PropertyCondition]::new($name, 'Confirm 1 project')
        $Window.FindAll([Windows.Automation.TreeScope]::Descendants, $condition).Count -eq 0
    } | Out-Null
    Invoke-Button $Window 'Preview projects'
    Find-Control $Window $name 'Confirm 1 project' -Button | Out-Null
    Invoke-Button $Window 'Cancel Bulk Add'
    Set-Field $Window 'project-search' 'SYN-BULK'
    Invoke-Button $Window 'Search'
    Find-Control $Window $name 'No projects match your search.' | Out-Null

    Invoke-Button $Window 'Bulk Add Projects'
    Set-Field $Window 'bulk-text' $content
    Invoke-Button $Window 'Preview projects'
    Invoke-Button $Window 'Confirm 1 project'
    Find-Control $Window $name 'SYN-BULK-0002' -Button | Out-Null
    Find-Control $Window $name ('SYN-BULK-0002 {0} Synthetic bulk yard' -f [char]0x00B7) | Out-Null
    Assert-TableColumn $Window 'Unscheduled projects' 1 @('0002')
    Invoke-Button $Window 'Bulk Add Projects'
    Set-Field $Window 'bulk-text' $content
    Invoke-Button $Window 'Preview projects'
    $confirm = Find-Control $Window $name 'Confirm 0 projects' -Button
    if ($confirm.Current.IsEnabled) { throw 'Duplicate-only synthetic batch could be confirmed.' }
    Invoke-Button $Window 'Cancel Bulk Add'

    Invoke-Button $Window 'Bulk Add Projects'
    $tsv = "Project Number`tSite ID`tSite Name`r`n000071`t0007`tNorth TSV yard`r`n000072`t0008`tWest TSV yard, Phase 2`r`n"
    Set-Field $Window 'bulk-text' $tsv
    Invoke-Button $Window 'Preview projects'
    Invoke-Button $Window 'Confirm 2 projects'
    Find-Control $Window $name '000071' -Button | Out-Null
    Invoke-Button $Window 'Bulk Add Projects'
    Set-Field $Window 'bulk-text' $tsv
    Invoke-Button $Window 'Preview projects'
    $confirmTsv = Find-Control $Window $name 'Confirm 0 projects' -Button
    if ($confirmTsv.Current.IsEnabled) { throw 'Repeated TSV batch could be confirmed.' }
    Invoke-Button $Window 'Cancel Bulk Add'
    Set-Field $Window 'project-search' '0042'
    Invoke-Button $Window 'Search'
    Find-Control $Window $name ('DEMO-26001 {0} Edited synthetic yard' -f [char]0x00B7) | Out-Null
    Find-Control $Window $name 'Small' | Out-Null
    Write-AcceptanceEvent 'PASS' 'bulk-projects' $timer 0 'preview=readonly edit=invalidated cancel=readonly confirm=eligibleOnly existing=preserved repeatedBatch=skipped'
}

function Test-ProjectSorting($Window) {
    Invoke-Button $Window 'Projects'
    Invoke-Button $Window 'New project'
    Set-Field $Window 'job_number' 'SYN-SORT-2'
    Set-Field $Window 'site_id' '02'
    Set-Field $Window 'site_name' 'Synthetic sort Z'
    Invoke-Button $Window 'Add work item'
    Set-Field $Window 'crews-0' '10'
    Set-Field $Window 'half-days-0' '20'
    Invoke-Button $Window 'Add work item'
    Set-Field $Window 'crews-1' '2'
    Set-Field $Window 'half-days-1' '4'
    Invoke-Button $Window 'Save project'
    Find-Control $Window $name ('SYN-SORT-2 {0} Synthetic sort Z' -f [char]0x00B7) | Out-Null
    Invoke-Button $Window 'New project'
    Set-Field $Window 'job_number' 'SYN-SORT-10'
    Set-Field $Window 'site_id' '10'
    Set-Field $Window 'site_name' 'Synthetic sort A'
    Invoke-Button $Window 'Save project'
    Find-Control $Window $name ('SYN-SORT-10 {0} Synthetic sort A' -f [char]0x00B7) | Out-Null
    Invoke-Button $Window 'SYN-SORT-2'
    Set-Field $Window 'project-search' 'sort'
    Invoke-Button $Window 'Search'
    Find-Control $Window $name '2 projects' | Out-Null

    Invoke-Button $Window 'Sort work items by Estimated half-days ascending'
    Assert-TableColumn $Window 'Project work items' 2 @('4', '20')
    Invoke-Button $Window 'Sort work items by Estimated half-days descending'
    Assert-TableColumn $Window 'Project work items' 2 @('20', '4')
    Invoke-Button $Window 'Sort work items by Required crews ascending'
    Assert-TableColumn $Window 'Project work items' 1 @('2', '10')
    Invoke-Button $Window 'Sort work items by Required crews descending'
    Assert-TableColumn $Window 'Project work items' 1 @('10', '2')

    foreach ($column in @(
        @{ Label = 'Job #'; First = 'SYN-SORT-10'; Last = 'SYN-SORT-2' },
        @{ Label = 'Site ID'; First = 'SYN-SORT-2'; Last = 'SYN-SORT-10' },
        @{ Label = 'Site name'; First = 'SYN-SORT-10'; Last = 'SYN-SORT-2' },
        @{ Label = 'Work items'; First = 'SYN-SORT-10'; Last = 'SYN-SORT-2' }
    )) {
        Invoke-Button $Window "Sort projects by $($column.Label) ascending"
        Assert-TableColumn $Window 'Unscheduled projects' 0 @($column.First, $column.Last)
        Invoke-Button $Window "Sort projects by $($column.Label) descending"
        Assert-TableColumn $Window 'Unscheduled projects' 0 @($column.Last, $column.First)
        Find-Control $Window $name ('SYN-SORT-2 {0} Synthetic sort Z' -f [char]0x00B7) | Out-Null
        Assert-TableColumn $Window 'Project work items' 1 @('10', '2')
        $search = (Find-Control $Window $automationId 'project-search').GetCurrentPattern($valuePattern)
        if ($search.Current.Value -cne 'sort') { throw 'Synthetic search changed during sorting.' }
    }
    # Type sorting must not reset the project sort or selected detail.
    Invoke-Button $Window 'Sort work items by Type ascending'
    Invoke-Button $Window 'Sort work items by Type descending'
    Assert-TableColumn $Window 'Unscheduled projects' 0 @('SYN-SORT-2', 'SYN-SORT-10')
    Find-Control $Window $name ('SYN-SORT-2 {0} Synthetic sort Z' -f [char]0x00B7) | Out-Null
    Write-AcceptanceEvent 'PASS' 'project-sorting' $timer 0 'bothTables=independent numericOrder=verified filter=preserved selectedProject=preserved'
}


Write-Host "Diagnostic log: $acceptanceLog"
Write-AcceptanceEvent 'INFO' 'gui-configuration' $null 0 "profile=$Profile guiSeconds=$($waits.GuiTimeoutSeconds) exitSeconds=$($waits.ExitTimeoutSeconds)"
$timer = [Diagnostics.Stopwatch]::StartNew()
$process = $null
$sidecar = $null
$runRoot = $null
$exitCode = 0
$phase = 'desktop-launch'
$requestedScopes = $PSBoundParameters
try {
    if ($ReproduceCrewChoice -and @($requestedScopes.Keys | Where-Object { $_ -like 'Include*' -and $requestedScopes[$_] }).Count) {
        Stop-Acceptance 'FAIL' 'configuration' $timer 0 'conflictingScopes=true'
    }
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
    if ($ReproduceCrewChoice) {
        $sidecar = Wait-For 'sidecar-process' { Get-Sidecar $process }
        Test-CrewChoiceReproduction $window
        Close-Dashboard $process
        exit 0
    }
    Invoke-Button $window 'Data'
    Invoke-Button $window 'Demo note'
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
    if ($IncludeProjects -or $IncludeProjectSorting -or $IncludeBulkProjects -or $IncludeProjectValidation) { Test-Projects $window }
    if ($IncludeProjectValidation) { Test-ProjectValidation $window }
    if ($IncludeProjectSorting) { Test-ProjectSorting $window }
    if ($IncludeBulkProjects) { Test-BulkProjects $window }
    if ($IncludeCrews -or $IncludeForemen) { Test-Crews $window }
    if ($IncludeForemen) { Test-Foremen $window }
    if ($IncludeStaffing -and -not $IncludeForemen) { Initialize-SyntheticStaffingPeople $window }
    if ($IncludeAssignments) { Test-Assignments $window }
    if ($IncludeMultiDay) { Test-MultiDayAssignments $window }
    if ($IncludeAvailability) { Test-Availability $window }
    if ($IncludeStaffing) { Test-Staffing $window }
    if ($IncludeEmployeeWeek) { Test-EmployeeWeek $window }
    if ($IncludeWorkingCalendars) { Test-WorkingCalendars $window }
    Close-Dashboard $process
    $process.Dispose()
    $process = $null
    $sidecar.Dispose()
    $sidecar = $null

    $process = Start-Dashboard
    Write-AcceptanceEvent 'START' 'desktop-reopen' $timer 0 (Get-AcceptanceProcessState $process)
    $window = Get-DashboardWindow $process
    Invoke-Button $window 'Data'
    Invoke-Button $window 'Demo note'
    Find-Control $window $name 'DEMO-001' | Out-Null
    $sidecar = Wait-For 'sidecar-process' { Get-Sidecar $process }
    $note = (Find-Control $window $automationId 'demo-note').GetCurrentPattern($valuePattern)
    if ($note.Current.Value -ne $newNote) {
        Stop-Acceptance 'FAIL' 'note-reopen' $timer 0 'savedNoteMismatch=true'
    }
    if ($IncludeProjects -or $IncludeProjectSorting -or $IncludeBulkProjects -or $IncludeProjectValidation) {
        Invoke-Button $window 'Projects'
        # TSV identifiers sort before the preserved Project Master fixture.
        if ($IncludeBulkProjects) { Invoke-Button $window 'DEMO-26001' }
        Find-Control $window $name ("DEMO-26001 {0} Edited synthetic yard" -f [char]0x00B7) | Out-Null
        Find-Control $window $name 'Small' | Out-Null
        Write-AcceptanceEvent 'PASS' 'project-master' $timer 0 'syntheticProjectAndWorkItem=reopened'
    }
    if ($IncludeBulkProjects) {
        Invoke-Button $window 'SYN-BULK-0002'
        Find-Control $window $name ('SYN-BULK-0002 {0} Synthetic bulk yard' -f [char]0x00B7) | Out-Null
        Set-Field $window 'project-search' 'SYN-BULK'
        Invoke-Button $window 'Search'
        Assert-TableColumn $window 'Unscheduled projects' 1 @('0002')
        Write-AcceptanceEvent 'PASS' 'bulk-projects-reopen' $timer 0 'syntheticProject=preserved leadingZeroes=preserved'
        Set-Field $window 'project-search' '000071'
        Invoke-Button $window 'Search'
        Invoke-Button $window '000071'
        Assert-TableColumn $window 'Unscheduled projects' 1 @('0007')
        Write-AcceptanceEvent 'PASS' 'clipboard-tsv-reopen' $timer 0 'copiedExamples=exactDelimiters tooltip=escapeDismissed tsv=confirmed leadingZeroes=preserved'
    }
    if ($IncludeProjectValidation) {
        Invoke-Button $window 'Projects'
        Set-Field $window 'project-search' 'UX-65-NEW'
        Invoke-Button $window 'Search'
        Invoke-Button $window 'UX-65-NEW'
        Assert-TableColumn $window 'Project work items' 1 @('2', '3')
        Assert-TableColumn $window 'Project work items' 2 @('4', '6')
        Write-AcceptanceEvent 'PASS' 'project-validation-reopen' $timer 0 'validProjectAndWorkItems=preserved'
    }
    if ($IncludeCrews -or $IncludeForemen) {
        Invoke-Button $window 'Crews'
        Find-Control $window $name 'Edit Synthetic Civil 02' | Out-Null
        Write-AcceptanceEvent 'PASS' 'crew-roster' $timer 0 'syntheticCrew=reopened'
    }
    if ($IncludeForemen) {
        Open-SyntheticForeman $window
        Assert-TableColumn $window 'Foreman change records' 2 @('Synthetic Foreman A (#1)', 'Unassigned', 'Synthetic Foreman B (#2)', 'Synthetic Foreman A (#1)')
        Write-AcceptanceEvent 'PASS' 'foreman-reopen' $timer 0 'appointmentAndFourHistoryEntries=preserved'
    }
    if ($IncludeAssignments) { Test-AssignmentsReopened $window }
    if ($IncludeMultiDay) { Test-MultiDayReopened $window }
    if ($IncludeStaffing) { Test-StaffingReopened $window }
    if ($IncludeAvailability) { Test-AvailabilityReopened $window }
    if ($IncludeEmployeeWeek) { Test-EmployeeWeek $window }
    if ($IncludeWorkingCalendars) { Test-WorkingCalendarsReopened $window }
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
    Invoke-Button $window 'Data'
    Invoke-Button $window 'Demo note'
    Find-Control $window $name 'Unable to open the local database. Check folder permissions and close other Rigarus windows.' | Out-Null
    Find-Control $window $name 'Retry' | Out-Null
    Close-Dashboard $process
    Write-AcceptanceEvent 'PASS' 'desktop-smoke' $timer 0 'note=reopened sidecar=exited startupError=displayed'
}
catch {
    Write-UiaFailure $_ $uiaLastOperation $window $uiaLastControl $uiaLastOption
    $exitCode = Get-AcceptanceExitCode $_ $phase $timer
}
finally {
    Stop-AcceptanceProcess $process 'desktop-cleanup' $waits.ExitTimeoutSeconds
    Stop-AcceptanceProcess $sidecar 'sidecar-cleanup' $waits.ExitTimeoutSeconds
    if ($runRoot -and (Test-Path -LiteralPath $runRoot -PathType Container)) {
        $resolvedRoot = (Resolve-Path -LiteralPath $runRoot).Path
        $temporaryParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
        if ((Split-Path -Parent $resolvedRoot) -eq $temporaryParent -and
            (Split-Path -Leaf $resolvedRoot) -match '^rigarus-tauri-smoke-[0-9a-f]{32}$') {
            if ($PreserveSyntheticProfile) {
                Write-Host ("Synthetic profile retained: " + $resolvedRoot)
                Write-AcceptanceEvent 'INFO' 'synthetic-profile-retained' $timer 0 ("profile=" + (Split-Path -Leaf $resolvedRoot))
            }
            else { Remove-Item -LiteralPath $resolvedRoot -Recurse -Force -ErrorAction SilentlyContinue }
        }
        else { Write-Warning 'Synthetic cleanup path did not match the expected temporary directory.' }
    }
}
exit $exitCode
