$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'TauriAcceptanceSupport.ps1')
. (Join-Path $PSScriptRoot 'TauriUiaDiagnostics.ps1')
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('rigarus-uia-harness-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testRoot | Out-Null
$uiaDiagnosticLog = Join-Path $testRoot 'synthetic.jsonl'
try {
    $inner = [InvalidOperationException]::new('Synthetic inner token=private-test-value')
    $outer = [Reflection.TargetInvocationException]::new('Synthetic wrapper', $inner)
    $chain = @(Get-UiaExceptionChain $outer)
    if ($chain.Count -ne 2 -or $chain[1].parent -ne 0 -or
        $chain[1].message -notmatch 'token=<redacted>' -or $chain[0].type -notmatch 'TargetInvocationException') {
        throw 'Nested exception diagnostics lost structure or secret redaction.'
    }
    $aggregate = [AggregateException]::new('Synthetic parallel failures', [Exception[]]@($inner, [ArgumentException]::new('Synthetic second')))
    if (@(Get-UiaExceptionChain $aggregate).Count -ne 3) { throw 'Aggregate inner exceptions were lost.' }
    try { throw $outer }
    catch { Write-UiaFailure $_ 'synthetic-boundary' $null }
    $record = Get-Content -LiteralPath $uiaDiagnosticLog -Tail 1 | ConvertFrom-Json
    if ($record.kind -ne 'exception' -or -not $record.data.invocation.line -or
        -not $record.data.invocation.scriptStackTrace -or $record.data.chain.Count -ne 2) {
        throw 'Exception invocation/stack/chain evidence is incomplete.'
    }
    $raw = Get-Content -LiteralPath $uiaDiagnosticLog -Raw
    if ($raw.Contains('private-test-value')) { throw 'Synthetic secret was written to diagnostic log.' }
    $safe = Protect-UiaDiagnosticText ('Bearer private-test-value password=private-test-value C:\Users\SyntheticUser\test ' + $env:USERPROFILE)
    if ($safe.Contains('private-test-value') -or $safe.Contains('SyntheticUser') -or $safe.Contains($env:USERPROFILE)) {
        throw 'Credential/profile redaction failed.'
    }
    Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
    if (-not [Windows.Automation.Automation].GetMethod('Compare', [type[]]@(
                [Windows.Automation.AutomationElement], [Windows.Automation.AutomationElement]))) {
        throw 'Owned-focus comparison API is unavailable.'
    }
    $healthy = [pscustomobject]@{}
    $healthy | Add-Member ScriptMethod GetCurrentPropertyValue {
        param($Property)
        if ($Property -eq [Windows.Automation.AutomationElement]::AutomationIdProperty) { return 'synthetic-choice' }
        'Synthetic property'
    }
    $healthy | Add-Member ScriptMethod GetRuntimeId { @(1, 2, 3) }
    $healthy | Add-Member ScriptMethod GetSupportedPatterns { @() }
    $healthy | Add-Member ScriptMethod TryGetCurrentPattern { param($Pattern, $Value) $false }
    $snapshot = Get-UiaElementSnapshot $healthy
    if ($snapshot.AutomationId -cne 'synthetic-choice' -or $snapshot.runtimeId.Count -ne 3) {
        throw 'Healthy target property/runtime identity was not captured.'
    }
    # The calendar timeout must resolve the actual owner, not the preceding scope.
    $ownerWindow = [pscustomobject]@{ target = $healthy }
    $ownerWindow | Add-Member ScriptMethod FindAll { param($Scope, $Condition) @($this.target) }
    try { throw [TimeoutException]::new('Synthetic Project choice timeout') }
    catch { Write-UiaFailure $_ 'choice:working-owner:verified-or-failed' $ownerWindow $healthy }
    $ownerFailure = Get-Content -LiteralPath $uiaDiagnosticLog -Tail 1 | ConvertFrom-Json
    if ($ownerFailure.data.targetId -cne 'working-owner' -or
        $ownerFailure.data.freshlyResolved.count -ne 1 -or
        $ownerFailure.data.freshlyResolved.control.runtimeId.Count -ne 3 -or
        $ownerFailure.data.chain[0].type -cne 'System.TimeoutException') {
        throw 'Project timeout lost the actual target, fresh provider or original exception.'
    }
    $stale = [pscustomobject]@{}
    $stale | Add-Member ScriptMethod GetCurrentPropertyValue { param($Property) throw [Windows.Automation.ElementNotAvailableException]::new('Synthetic element detached') }
    $snapshot = Get-UiaElementSnapshot $stale
    if (-not $snapshot.present -or -not $snapshot.AutomationId.error) {
        throw 'Unavailable target lost its diagnostic error instead of recording it.'
    }
    $ownerWindow | Add-Member ScriptMethod FindFirst { param($Scope, $Condition) $this.target }
    $healthy | Add-Member ScriptMethod FindAll { param($Scope, $Condition) @($this) * 121 }
    & {
        # No desktop-wide focus inspection in the synthetic harness.
        function Get-UiaFocusedElement { $null }
        Write-UiaChoiceState 'synthetic-detached' $ownerWindow $stale 'working-owner' ([Diagnostics.Stopwatch]::StartNew())
    }
    $choiceState = (Get-Content -LiteralPath $uiaDiagnosticLog -Tail 1 | ConvertFrom-Json).data
    if ($choiceState.targetId -cne 'working-owner' -or $choiceState.focusOwned -or $choiceState.focused -or
        -not $choiceState.original.AutomationId.error -or -not $choiceState.freshlyResolved.present -or
        $choiceState.exposedChildCount -ne 121 -or $choiceState.exposedChildren.Count -ne 120 -or
        -not $choiceState.childrenTruncated -or $null -eq $choiceState.elapsedMs) {
        throw 'Detached-target evidence, owned-focus privacy or child snapshot bound failed.'
    }
    $installer = Join-Path $testRoot 'synthetic-installer.exe'
    Set-Content -LiteralPath $installer -Value 'Synthetic package fixture, never executed'
    $kit = Join-Path $testRoot 'kit'
    & (Join-Path $PSScriptRoot 'New-TauriAcceptanceKit.ps1') -Installer $installer -Commit ('a' * 40) -OutputDirectory $kit
    if ((Get-FileHash (Join-Path $kit 'TauriUiaDiagnostics.ps1')).Hash -ne
        (Get-FileHash (Join-Path $PSScriptRoot 'TauriUiaDiagnostics.ps1')).Hash) {
        throw 'Generated acceptance kit cannot load its matching diagnostic support.'
    }
    if (-not (Test-UiaChoiceLabel 'Synthetic Crew (Civil #7)' 'Synthetic Crew') -or
        -not (Test-UiaChoiceLabel ('Synthetic Person (#2) ' + [char]0x00B7 + ' Inactive') 'Synthetic Person (#2)') -or
        (Test-UiaChoiceLabel 'Synthetic Crew Extra (Civil #8)' 'Synthetic Crew')) {
        throw 'Choice verification confused a different label with the intended selection.'
    }
    $acceptanceLog = Join-Path $testRoot 'retry.log'
    foreach ($failure in @([InvalidOperationException]::new('Synthetic UIA Expand rejected'),
        [Windows.Automation.ElementNotAvailableException]::new('Synthetic detached provider'),
        [Windows.Automation.ElementNotEnabledException]::new('Synthetic temporarily disabled provider'))) {
        $state = @{ attempts = 0; retries = 0; selected = 0 }
        Wait-AcceptanceProbe 'synthetic-choice' 2 {
            Invoke-UiaTransientProbe {
                $state.attempts++
                if ($state.attempts -eq 1) { throw [Reflection.TargetInvocationException]::new('Synthetic wrapper', $failure) }
                $state.selected++; $true
            } { param($record) $state.retries++ }
        } { 'process=synthetic target=crew' } | Out-Null
        if ($state.attempts -ne 2 -or $state.retries -ne 1 -or $state.selected -ne 1) {
            throw 'Transient UIA rejection was not retried once before a single successful action.'
        }
    }
    foreach ($failure in @([ArgumentException]::new('Synthetic programming error'),
        [UnauthorizedAccessException]::new('Synthetic denied action'),
        [NotSupportedException]::new('Synthetic unsupported pattern'))) {
        $state = @{ retries = 0 }; $rejected = $false
        try { Invoke-UiaTransientProbe { throw $failure } { param($record) $state.retries++ } | Out-Null }
        catch { $rejected = $true }
        if (-not $rejected -or $state.retries) { throw 'Unknown/denied/unsupported failure was swallowed.' }
    }
    $state = @{ attempts = 0 }; $timedOut = $false
    $bound = [Diagnostics.Stopwatch]::StartNew()
    try {
        Wait-AcceptanceProbe 'synthetic-choice' 1 {
            Invoke-UiaTransientProbe {
                $state.attempts++; throw [InvalidOperationException]::new('Synthetic permanent provider failure')
            } { param($record) }
        } { 'process=synthetic target=crew' } | Out-Null
    }
    catch { $timedOut = $_.Exception.Data['AcceptanceStatus'] -eq 'TIMEOUT' }
    if (-not $timedOut -or $state.attempts -lt 2 -or $bound.Elapsed.TotalSeconds -gt 5) {
        throw 'Persistent provider failure escaped the bounded timeout or incorrectly passed.'
    }
    $timeout = [InvalidOperationException]::new('Synthetic acceptance timeout')
    $timeout.Data['AcceptanceStatus'] = 'TIMEOUT'
    if (Test-UiaTransientException $timeout) { throw 'Acceptance timeout must never be retried as UIA readiness.' }
    $tokens = $null; $parseErrors = $null
    $desktopAst = [Management.Automation.Language.Parser]::ParseFile(
        (Join-Path $PSScriptRoot 'Test-TauriDesktop.ps1'), [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors.Count) { throw 'Desktop verifier does not parse.' }
    if (-not ('RigarusAcceptanceWindow' -as [type])) {
        $nativeSource = $desktopAst.FindAll({ param($node)
            $node -is [Management.Automation.Language.StringConstantExpressionAst] -and
            $node.Value.Contains('class RigarusAcceptanceWindow')
        }, $true) | Select-Object -First 1
        Add-Type -TypeDefinition $nativeSource.Value
    }
    $restore = $desktopAst.EndBlock.Statements | Where-Object {
        $_ -is [Management.Automation.Language.FunctionDefinitionAst] -and $_.Name -eq 'Restore-AcceptanceWindow'
    }
    Invoke-Expression $restore.Extent.Text
    $script:uiaOwnedHandle = [IntPtr](-1); $script:uiaOwnedWindow = $null
    $ownershipRejected = $false
    try { Restore-AcceptanceWindow ([pscustomobject]@{ Id = 123 }) }
    catch { $ownershipRejected = $_.Exception.Message -eq 'Verifier window ownership changed.' }
    finally { $script:uiaOwnedHandle = [IntPtr]::Zero }
    if (-not $ownershipRejected) { throw 'A foreign/invalid window was not rejected before restore.' }
    $scopeLog = Join-Path $testRoot 'scope.log'
    $scopeArgs = '-NoProfile -STA -File "' + (Join-Path $kit 'Test-TauriDesktop.ps1') +
        '" -Executable "synthetic-not-started.exe" -ReproduceCrewChoice -IncludeEmployeeWeek -DiagnosticLog "' + $scopeLog + '"'
    $scopeCheck = Start-Process powershell.exe -ArgumentList $scopeArgs -WindowStyle Hidden -PassThru
    try {
        $null = $scopeCheck.Handle
        if (-not $scopeCheck.WaitForExit(15000)) { throw 'Conflicting-scope check exceeded its limit.' }
        if ($scopeCheck.ExitCode -ne 1 -or
            (Get-Content -LiteralPath $scopeLog -Tail 1) -notmatch 'phase=configuration .*conflictingScopes=true$') {
            throw 'Minimal reproduction silently replaced requested full coverage.'
        }
    }
    finally { Stop-AcceptanceProcess $scopeCheck 'synthetic-scope-cleanup' 5 }
    Write-Host 'PASS: UIA nested/aggregate chains, invocation/stack, detached target and local-log redaction.'
    Write-Host 'PASS: Transient Expand/detached/disabled recovery, strict labels, hard failures and bounded persistent failure.'
}
finally {
    $resolved = [IO.Path]::GetFullPath($testRoot)
    $parent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
    if ((Split-Path -Parent $resolved) -ne $parent -or
        (Split-Path -Leaf $resolved) -notmatch '^rigarus-uia-harness-[0-9a-f]{32}$') { throw 'Unsafe synthetic cleanup path' }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
