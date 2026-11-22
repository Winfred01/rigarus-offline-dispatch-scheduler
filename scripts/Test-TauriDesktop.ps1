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
    if ($IncludeProjects -or $IncludeProjectSorting -or $IncludeBulkProjects -or $IncludeProjectValidation) { Test-Projects $window }
    if ($IncludeProjectValidation) { Test-ProjectValidation $window }
    if ($IncludeProjectSorting) { Test-ProjectSorting $window }
    if ($IncludeBulkProjects) { Test-BulkProjects $window }
    if ($IncludeCrews -or $IncludeForemen) { Test-Crews $window }
    if ($IncludeForemen) { Test-Foremen $window }
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
        $resolvedRoot = (Resolve-Path -LiteralPath $runRoot).Path
        $temporaryParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
        if ((Split-Path -Parent $resolvedRoot) -eq $temporaryParent -and
            (Split-Path -Leaf $resolvedRoot) -match '^rigarus-tauri-smoke-[0-9a-f]{32}$') {
            Remove-Item -LiteralPath $resolvedRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
        else { Write-Warning 'Synthetic cleanup path did not match the expected temporary directory.' }
    }
}
exit $exitCode
