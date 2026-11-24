$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
. (Join-Path $PSScriptRoot 'TauriAcceptanceSupport.ps1')
. (Join-Path $PSScriptRoot 'TauriUiaDiagnostics.ps1')
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('rigarus-project-choice-harness-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testRoot | Out-Null
try {
    $tokens = $null; $errors = $null
    $ast = [Management.Automation.Language.Parser]::ParseFile(
        (Join-Path $PSScriptRoot 'Test-TauriDesktop.ps1'), [ref]$tokens, [ref]$errors)
    if ($errors.Count) { throw 'Project verifier does not parse.' }
    foreach ($functionName in @('Wait-For', 'Get-WorkingProjectPattern', 'Wait-WorkingProjectState', 'Select-WorkingProject')) {
        $node = $ast.FindAll({ param($n)
            $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $functionName
        }, $false)
        if (@($node).Count -ne 1) { throw 'Missing/ambiguous real Project verifier function.' }
        Invoke-Expression $node.Extent.Text
    }
    & {
        # Fake providers model the actual silent no-effect and transient failures.
        # No keyboard, foreign-window inspection or application launch occurs here.
        $automationId = [Windows.Automation.AutomationElement]::AutomationIdProperty
        $valuePattern = [Windows.Automation.ValuePattern]::Pattern
        $process = [pscustomobject]@{ HasExited = $false; MainWindowHandle = [IntPtr]::Zero }
        $sidecar = $null
        function Restore-AcceptanceWindow($Process) { }
        function Get-AcceptanceProcessState($Process) { 'process=synthetic' }
        function Get-UiaElementSnapshot($Element) { @{ present = $true } }
        function Test-UiaOwnedForeground { $model.foreground }
        function Get-UiaFocusedElement { [pscustomobject]@{ Current = [pscustomobject]@{ AutomationId = $model.focused } } }
        function Write-UiaChoiceState { param($Stage, $Window, $Control, $Id, $Timer, [switch]$OmitChildren) }
        function Write-UiaFailure { param($ErrorRecord, $Operation, $Window, $Control, $Option, $Disposition)
            if ($Disposition -eq 'retrying') { $model.transientFailures++ }
        }
        function Send-WorkingProjectKeys([string]$Keys) {
            $model.keys.Add($Keys)
            if ($Keys -eq 'SYN-14-UI') {
                if (-not $model.ignoreText) {
                    $model.value.Current.Value = if ($model.wrongText) { 'SYN-14-UI-OTHER' } else { $model.expected }
                }
                if ($model.textCloses) { $model.expand.Current.ExpandCollapseState = [Windows.Automation.ExpandCollapseState]::Collapsed }
                if ($model.loseForeground) { $model.foreground = $false }
            }
            elseif ($Keys -eq '{ENTER}') {
                if (-not $model.ignoreEnter) { $model.expand.Current.ExpandCollapseState = [Windows.Automation.ExpandCollapseState]::Collapsed }
                if ($model.wrongCommit) { $model.value.Current.Value = 'Synthetic other Project' }
            }
            else { throw 'Unexpected or combined synthetic key batch.' }
        }
        function New-ProjectModel {
            $m = [pscustomobject]@{
                expected = ('SYN-14-UI ' + [char]0x00B7 + ' Synthetic site (#101)')
                keys = [Collections.Generic.List[string]]::new(); foreground = $true; focused = ''
                missing = $false; ambiguous = $false; neverFocus = $false; neverExpand = $false
                ignoreText = $false; wrongText = $false; ignoreEnter = $false; wrongCommit = $false
                textCloses = $false; loseForeground = $false; unsupportedValue = $false; unsupportedExpand = $false
                silentExpands = 0; transientOnce = $false; transientAfterEffect = $false; unknownExpand = $false
                focusDelayMs = 0; expandDelayMs = 0; focusCalls = 0; expandCalls = 0; transientFailures = 0; resolves = 0
                value = [pscustomobject]@{ Current = [pscustomobject]@{ Value = 'Select a Project' } }
                expand = [pscustomobject]@{ Current = [pscustomobject]@{ ExpandCollapseState = [Windows.Automation.ExpandCollapseState]::Collapsed } }
                control = $null; window = $null
            }
            $m.expand | Add-Member NoteProperty model $m
            $m.expand | Add-Member ScriptMethod Expand {
                $m = $this.model; $m.expandCalls++
                if ($m.expandDelayMs) { Start-Sleep -Milliseconds $m.expandDelayMs }
                if ($m.unknownExpand) { throw [ArgumentException]::new('Synthetic unknown provider failure') }
                if ($m.transientAfterEffect -and $m.expandCalls -eq 1) {
                    $this.Current.ExpandCollapseState = [Windows.Automation.ExpandCollapseState]::Expanded
                    throw [InvalidOperationException]::new('Synthetic refusal after state changed')
                }
                if ($m.transientOnce -and $m.expandCalls -eq 1) { throw [InvalidOperationException]::new('Synthetic operation refusal') }
                if (-not $m.neverExpand -and $m.expandCalls -gt $m.silentExpands) {
                    $this.Current.ExpandCollapseState = [Windows.Automation.ExpandCollapseState]::Expanded
                }
            }
            $m.expand | Add-Member ScriptMethod Collapse { throw 'Project protocol must not force provider Collapse.' }
            $m.control = [pscustomobject]@{ model = $m; Current = [pscustomobject]@{ IsEnabled = $true } }
            $m.control | Add-Member ScriptMethod SetFocus {
                $this.model.focusCalls++
                if ($this.model.focusDelayMs) { Start-Sleep -Milliseconds $this.model.focusDelayMs }
                if (-not $this.model.neverFocus) { $this.model.focused = 'working-owner' }
            }
            $m.control | Add-Member ScriptMethod TryGetCurrentPattern {
                param($Pattern, $Result)
                if ($Pattern -eq [Windows.Automation.ValuePattern]::Pattern -and -not $this.model.unsupportedValue) {
                    $Result.Value = $this.model.value; return $true
                }
                if ($Pattern -eq [Windows.Automation.ExpandCollapsePattern]::Pattern -and -not $this.model.unsupportedExpand) {
                    $Result.Value = $this.model.expand; return $true
                }
                $false
            }
            $m.window = [pscustomobject]@{ model = $m }
            $m.window | Add-Member ScriptMethod FindAll {
                param($Scope, $Condition)
                $this.model.resolves++
                if ($this.model.missing) { return @() }
                if ($this.model.ambiguous) { return @($this.model.control, $this.model.control) }
                @($this.model.control)
            }
            $m
        }
        $cases = @(
            @{ Name = 'normal'; Code = 0; Keys = 2; Setup = { } },
            @{ Name = 'silent-expand'; Code = 0; Keys = 2; Setup = { $model.silentExpands = 2 } },
            @{ Name = 'transient-expand'; Code = 0; Keys = 2; Setup = { $model.transientOnce = $true } },
            @{ Name = 'transient-after-effect'; Code = 0; Keys = 2; Setup = { $model.transientAfterEffect = $true } },
            @{ Name = 'never-expand'; Code = 2; Keys = 0; Setup = { $model.neverExpand = $true } },
            @{ Name = 'never-focus'; Code = 2; Keys = 0; Setup = { $model.neverFocus = $true } },
            @{ Name = 'disabled'; Code = 2; Keys = 0; Setup = { $model.control.Current.IsEnabled = $false } },
            @{ Name = 'missing'; Code = 2; Keys = 0; Setup = { $model.missing = $true } },
            @{ Name = 'ambiguous'; Code = 1; Keys = 0; Setup = { $model.ambiguous = $true } },
            @{ Name = 'unsupported-value'; Code = 1; Keys = 0; Setup = { $model.unsupportedValue = $true } },
            @{ Name = 'unsupported-expand'; Code = 1; Keys = 0; Setup = { $model.unsupportedExpand = $true } },
            @{ Name = 'unknown'; Code = 1; Keys = 0; Setup = { $model.unknownExpand = $true } },
            @{ Name = 'foreign-foreground'; Code = 2; Keys = 0; Setup = { $model.foreground = $false } },
            @{ Name = 'no-text-response'; Code = 2; Keys = 1; Setup = { $model.ignoreText = $true } },
            @{ Name = 'wrong-label'; Code = 2; Keys = 1; Setup = { $model.wrongText = $true } },
            @{ Name = 'no-commit'; Code = 2; Keys = 2; Setup = { $model.ignoreEnter = $true } },
            @{ Name = 'wrong-committed-label'; Code = 2; Keys = 2; Setup = { $model.wrongCommit = $true } },
            @{ Name = 'already-committed-after-text'; Code = 0; Keys = 1; Setup = { $model.textCloses = $true } },
            @{ Name = 'lost-foreground'; Code = 2; Keys = 1; Setup = { $model.loseForeground = $true } },
            @{ Name = 'shared-deadline'; Code = 2; Keys = 0; Setup = { $model.focusDelayMs = 600; $model.expandDelayMs = 600 } }
        )
        foreach ($case in $cases) {
            $model = New-ProjectModel
            $waits = @{ GuiTimeoutSeconds = $(if ($case.Code -eq 0) { 3 } else { 1 }) }
            $acceptanceLog = Get-AcceptanceLogPath (Join-Path $testRoot ($case.Name + '.log'))
            & $case.Setup
            $code = 0
            try { Select-WorkingProject $model.window 'SYN-14-UI' }
            catch {
                $code = Get-AcceptanceExitCode $_ 'synthetic-project' $null
                if ($code -ne $case.Code) { Write-Host $_.Exception.ToString(); Write-Host $_.ScriptStackTrace }
            }
            if ($code -ne $case.Code -or $model.keys.Count -ne $case.Keys -or
                @($model.keys | Where-Object { $_ -eq 'SYN-14-UI' }).Count -gt 1 -or
                @($model.keys | Where-Object { $_ -eq '{ENTER}' }).Count -gt 1) {
                throw "Synthetic Project case $($case.Name): code=$code keys=$($model.keys.Count)"
            }
            if ($case.Name -eq 'silent-expand' -and ($model.expandCalls -ne 3 -or $model.resolves -le $model.expandCalls)) {
                throw 'Silent readiness refusal was not reacquired and acknowledged.'
            }
            if ($case.Name -eq 'transient-expand' -and $model.transientFailures -ne 1) { throw 'Transient refusal evidence was lost.' }
            if ($case.Name -eq 'transient-after-effect' -and ($model.transientFailures -ne 1 -or $model.expandCalls -ne 1)) {
                throw 'An already observed expansion was repeated after a provider refusal.'
            }
            if ($case.Name -eq 'unknown' -and $model.transientFailures) { throw 'Unknown provider error was retried.' }
            if ($code -eq 0 -and ($model.value.Current.Value -cne $model.expected -or
                    $model.expand.Current.ExpandCollapseState -ne [Windows.Automation.ExpandCollapseState]::Collapsed)) {
                throw 'A wrong/open Project selection was declared committed.'
            }
            Write-Host ('PASS: Project protocol ' + $case.Name)
        }
    }
}
finally {
    $resolved = [IO.Path]::GetFullPath($testRoot)
    $parent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
    if ((Split-Path -Parent $resolved) -ne $parent -or
        (Split-Path -Leaf $resolved) -notmatch '^rigarus-project-choice-harness-[0-9a-f]{32}$') { throw 'Unsafe synthetic cleanup path.' }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
