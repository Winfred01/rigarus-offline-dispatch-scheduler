# Detailed UIA evidence is local-only and used only with the verifier's synthetic profile.
function Protect-UiaDiagnosticText([string]$Text) {
    if (-not $Text) { return $Text }
    $result = $Text
    foreach ($path in @($env:LOCALAPPDATA, $env:TEMP, $env:USERPROFILE, $PSScriptRoot) |
        Where-Object { $_ } | Sort-Object Length -Descending -Unique) {
        $result = $result -replace [regex]::Escape($path), '<local>'
    }
    $result = $result -replace '(?i)[a-z]:[\\/]Users[\\/][^\\/\s"'']+', '<user>'
    $result = $result -replace 'rigarus-tauri-smoke-[0-9a-f]{32}', '<synthetic-profile>'
    $result = $result -replace '(?i)\bBearer\s+[a-z0-9._~+/-]+=*', 'Bearer <redacted>'
    $result = $result -replace '(?i)\b(password|token|authorization)\s*[:=]\s*[^\s,;"'']+', '$1=<redacted>'
    $result = $result -replace '\b[a-fA-F0-9]{64}\b', '<redacted-hex>'
    $result
}

function Write-UiaDiagnostic([string]$Kind, $Data) {
    if (-not $uiaDiagnosticLog) { return }
    $record = [ordered]@{ utc = [DateTime]::UtcNow.ToString('o'); kind = $Kind; data = $Data }
    $json = $record | ConvertTo-Json -Depth 24 -Compress
    # Sanitize strings before JSON encoding, not serialized JSON escape sequences.
    Add-Content -LiteralPath $uiaDiagnosticLog -Value $json -Encoding UTF8
}

function Get-UiaExceptionChain([Exception]$Exception) {
    $chain = @(); $seen = [Collections.Generic.HashSet[Exception]]::new()
    $pending = [Collections.Generic.Queue[object]]::new()
    $pending.Enqueue(@{ exception = $Exception; parent = $null })
    while ($pending.Count) {
        $item = $pending.Dequeue(); $current = $item.exception
        if (-not $current -or -not $seen.Add($current)) { continue }
        $index = $chain.Count
        $chain += [ordered]@{
            index = $index; parent = $item.parent; type = $current.GetType().FullName
            hresult = ('0x{0:X8}' -f $current.HResult)
            message = Protect-UiaDiagnosticText $current.Message
            stackTrace = Protect-UiaDiagnosticText $current.StackTrace
            source = Protect-UiaDiagnosticText $current.Source
        }
        if ($current -is [AggregateException]) {
            foreach ($inner in $current.InnerExceptions) { $pending.Enqueue(@{ exception = $inner; parent = $index }) }
        }
        elseif ($current.InnerException) { $pending.Enqueue(@{ exception = $current.InnerException; parent = $index }) }
    }
    $chain
}

function Get-UiaElementSnapshot($Element) {
    if (-not $Element) { return @{ present = $false } }
    $result = [ordered]@{ present = $true }
    foreach ($property in @('AutomationId', 'Name', 'ClassName', 'FrameworkId', 'ProcessId',
        'NativeWindowHandle', 'ControlType', 'IsEnabled', 'IsOffscreen', 'HasKeyboardFocus', 'IsKeyboardFocusable', 'BoundingRectangle')) {
        try {
            $uiaProperty = [Windows.Automation.AutomationElement]::($property + 'Property')
            $result[$property] = Protect-UiaDiagnosticText ([string]$Element.GetCurrentPropertyValue($uiaProperty))
        }
        catch { $result[$property] = @{ error = @(Get-UiaExceptionChain $_.Exception) } }
    }
    try { $result.runtimeId = @($Element.GetRuntimeId()) }
    catch { $result.runtimeIdError = @(Get-UiaExceptionChain $_.Exception) }
    $handle = 0
    if ([int]::TryParse([string]$result.NativeWindowHandle, [ref]$handle) -and $handle -ne 0) {
        if (-not ('RigarusUiaWindowState' -as [type])) {
            Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class RigarusUiaWindowState {
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr window);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
'@
        }
        $result.nativeVisible = [RigarusUiaWindowState]::IsWindowVisible([IntPtr]$handle)
        $result.isForeground = [RigarusUiaWindowState]::GetForegroundWindow() -eq [IntPtr]$handle
    }
    try {
        $result.patterns = @($Element.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName })
        $pattern = $null
        if ($Element.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern, [ref]$pattern)) {
            $result.value = Protect-UiaDiagnosticText ([string]$pattern.Current.Value)
        }
        $pattern = $null
        if ($Element.TryGetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern, [ref]$pattern)) {
            $result.isSelected = $pattern.Current.IsSelected
        }
        $pattern = $null
        if ($Element.TryGetCurrentPattern([Windows.Automation.ExpandCollapsePattern]::Pattern, [ref]$pattern)) {
            $result.expandState = [string]$pattern.Current.ExpandCollapseState
        }
    }
    catch { $result.patternError = @(Get-UiaExceptionChain $_.Exception) }
    $result
}

function Write-UiaOperation([string]$Operation, [string]$Stage, $Window, $Control, $Option = $null) {
    $script:uiaLastOperation = $Operation
    $script:uiaLastControl = $Control
    $script:uiaLastOption = $Option
    Write-UiaDiagnostic 'operation' ([ordered]@{
        operation = $Operation; stage = $Stage
        window = Get-UiaElementSnapshot $Window
        control = Get-UiaElementSnapshot $Control
        option = Get-UiaElementSnapshot $Option
    })
}

function Get-UiaFocusedElement {
    [Windows.Automation.AutomationElement]::FocusedElement
}

function Write-UiaChoiceState([string]$Stage, $Window, $Control, [string]$Id,
    [Diagnostics.Stopwatch]$Timer) {
    # Primitive snapshots only. Never serialize a UIA/provider object graph.
    $script:uiaLastOperation = "choice:${id}:$Stage"
    $script:uiaLastControl = $Control; $script:uiaLastOption = $null
    $record = [ordered]@{
        stage = $Stage; targetId = $id
        elapsedMs = $(if ($Timer) { $Timer.ElapsedMilliseconds } else { $null })
        window = Get-UiaElementSnapshot $Window
        original = Get-UiaElementSnapshot $Control
        focusOwned = $false; focused = $null
    }
    $fresh = $null
    try {
        $condition = [Windows.Automation.PropertyCondition]::new(
            [Windows.Automation.AutomationElement]::AutomationIdProperty, $id)
        $fresh = $Window.FindFirst([Windows.Automation.TreeScope]::Descendants, $condition)
        $record.freshlyResolved = Get-UiaElementSnapshot $fresh
        if ($fresh) { $script:uiaLastControl = $fresh }
    }
    catch { $record.resolveError = @(Get-UiaExceptionChain $_.Exception) }
    try {
        $focused = Get-UiaFocusedElement
        $ancestor = $focused
        for ($depth = 0; $ancestor -and $depth -lt 40; $depth++) {
            if ([Windows.Automation.Automation]::Compare($ancestor, $Window)) { $record.focusOwned = $true; break }
            $ancestor = [Windows.Automation.TreeWalker]::RawViewWalker.GetParent($ancestor)
        }
        if ($record.focusOwned) { $record.focused = Get-UiaElementSnapshot $focused }
    }
    catch { $record.focusError = @(Get-UiaExceptionChain $_.Exception) }
    try {
        if ($fresh) {
            $children = @($fresh.FindAll([Windows.Automation.TreeScope]::Children,
                    [Windows.Automation.Condition]::TrueCondition))
            $record.exposedChildCount = $children.Count
            $record.exposedChildren = @($children | Select-Object -First 120 | ForEach-Object { Get-UiaElementSnapshot $_ })
            $record.childrenTruncated = $children.Count -gt 120
        }
    }
    catch { $record.childrenError = @(Get-UiaExceptionChain $_.Exception) }
    Write-UiaDiagnostic 'choice-state' $record
}

function Write-UiaFailure($ErrorRecord, [string]$Operation, $Window, $Control = $null, $Option = $null, [string]$Disposition = 'fatal') {
    $fresh = $null; $targetId = $null
    if ($Window -and $Operation -match '^choice:([^:]+):') {
        $targetId = $Matches[1]
        try {
            $condition = [Windows.Automation.PropertyCondition]::new(
                [Windows.Automation.AutomationElement]::AutomationIdProperty, $targetId)
            $targets = @($Window.FindAll([Windows.Automation.TreeScope]::Descendants, $condition))
            $fresh = @{ count = $targets.Count; control = $(if ($targets.Count) { Get-UiaElementSnapshot $targets[0] } else { $null }) }
        }
        catch { $fresh = @{ error = @(Get-UiaExceptionChain $_.Exception) } }
    }
    Write-UiaDiagnostic 'exception' ([ordered]@{
        operation = $Operation
        disposition = $Disposition
        targetId = $targetId
        freshlyResolved = $fresh
        chain = @(Get-UiaExceptionChain $ErrorRecord.Exception)
        invocation = [ordered]@{
            script = Protect-UiaDiagnosticText $ErrorRecord.InvocationInfo.ScriptName
            line = $ErrorRecord.InvocationInfo.ScriptLineNumber
            offset = $ErrorRecord.InvocationInfo.OffsetInLine
            position = Protect-UiaDiagnosticText $ErrorRecord.InvocationInfo.PositionMessage
            command = Protect-UiaDiagnosticText ([string]$ErrorRecord.InvocationInfo.MyCommand)
            scriptStackTrace = Protect-UiaDiagnosticText $ErrorRecord.ScriptStackTrace
            category = [string]$ErrorRecord.CategoryInfo.Category
            errorId = Protect-UiaDiagnosticText $ErrorRecord.FullyQualifiedErrorId
        }
        windowAfter = Get-UiaElementSnapshot $Window
        controlAfter = Get-UiaElementSnapshot $Control
        optionAfter = Get-UiaElementSnapshot $Option
    })
}

# Only wrap non-persisting UIA reads/choice actions with this probe. Never wrap
# Save buttons, HTTP, SQLite, assertions or arbitrary application operations.
function Test-UiaTransientException([Exception]$Exception) {
    $seen = [Collections.Generic.HashSet[Exception]]::new()
    while ($Exception -and $seen.Add($Exception)) {
        if ($Exception.Data['AcceptanceStatus']) { return $false }
        if ($Exception -is [InvalidOperationException] -or
            $Exception -is [Windows.Automation.ElementNotAvailableException] -or
            $Exception -is [Windows.Automation.ElementNotEnabledException]) { return $true }
        if ($Exception -is [Runtime.InteropServices.COMException] -and
            $Exception.HResult -in @(-2147220992, -2147220991)) { return $true }
        $Exception = $Exception.InnerException
    }
    $false
}

function Invoke-UiaTransientProbe([scriptblock]$Action, [scriptblock]$OnTransient) {
    try { & $Action }
    catch {
        if (-not (Test-UiaTransientException $_.Exception)) { throw }
        & $OnTransient $_ | Out-Null
        $false
    }
}

function Test-UiaChoiceLabel([string]$Observed, [string]$Expected) {
    $Observed -ceq $Expected -or $Observed.StartsWith($Expected + ' (', [StringComparison]::Ordinal) -or
        $Observed.StartsWith($Expected + ' ' + [char]0x00B7 + ' ', [StringComparison]::Ordinal)
}
