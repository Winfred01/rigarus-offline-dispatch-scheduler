function Get-AcceptanceLogPath([string]$Path) {
    if (-not $Path) {
        $Path = Join-Path ([IO.Path]::GetTempPath()) ('rigarus-acceptance-' + [Guid]::NewGuid().ToString('N') + '.log')
    }
    $Path = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        New-Item -ItemType File -Path $Path | Out-Null
    }
    $Path
}

function Read-AcceptanceProgressText([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $line = Get-Content -LiteralPath $Path -Tail 1 -ErrorAction Stop
    if ($null -ne $line) {
        # Windows PowerShell strings from Get-Content carry Provider/Drive metadata.
        # Deep JSON serialization can traverse that graph instead of reporting text.
        # Explicitly materialize text before placing it in a progress record.
        return $line.ToString()
    }
}

function Get-AcceptanceWaits([string]$Profile, [System.Collections.IDictionary]$Overrides) {
    $waits = if ($Profile -eq 'SlowVm') {
        @{ InstallTimeoutSeconds = 900; GuiTimeoutSeconds = 150; ExitTimeoutSeconds = 60 }
    }
    else {
        @{ InstallTimeoutSeconds = 300; GuiTimeoutSeconds = 30; ExitTimeoutSeconds = 12 }
    }
    foreach ($key in @($waits.Keys)) {
        if ($Overrides.ContainsKey($key)) { $waits[$key] = $Overrides[$key] }
    }
    $waits
}

function Write-AcceptanceEvent([string]$Status, [string]$Phase, $Timer, [int]$LimitSeconds, [string]$State) {
    $elapsed = if ($Timer) { $Timer.ElapsedMilliseconds } else { 0 }
    $limit = if ($LimitSeconds) { " limitSeconds=$LimitSeconds" } else { '' }
    $line = "status=$Status phase=$Phase elapsedMs=$elapsed$limit state=$State"
    Write-Host $line
    if ($acceptanceLog) {
        # Windows PowerShell Add-Content can reject an existing supervisor reader.
        # One verifier appends while its supervisor reads; real I/O failures still throw.
        $stream = [IO.File]::Open($acceptanceLog, 'Append', 'Write', 'ReadWrite')
        $writer = $null
        try {
            $writer = [IO.StreamWriter]::new($stream, [Text.UTF8Encoding]::new($true))
            $writer.WriteLine($line)
        }
        finally {
            if ($writer) { $writer.Dispose() } else { $stream.Dispose() }
        }
    }
}

function Stop-Acceptance([string]$Status, [string]$Phase, $Timer, [int]$LimitSeconds, [string]$State) {
    Write-AcceptanceEvent $Status $Phase $Timer $LimitSeconds $State
    $exception = [InvalidOperationException]::new("$Status $Phase")
    $exception.Data['AcceptanceStatus'] = $Status
    throw $exception
}

function Get-AcceptanceExitCode($ErrorRecord, [string]$Phase, $Timer, [string]$UnexpectedStatus = 'FAIL') {
    $status = $ErrorRecord.Exception.Data['AcceptanceStatus']
    if (-not $status) {
        $status = $UnexpectedStatus
        Write-AcceptanceEvent $status $Phase $Timer 0 "exceptionType=$($ErrorRecord.Exception.GetType().Name)"
    }
    switch ($status) {
        'TIMEOUT' { 2 }
        'BLOCKED' { 3 }
        default { 1 }
    }
}

function Get-AcceptanceProcessState([Diagnostics.Process]$Process) {
    if (-not $Process) { return 'process=not-started' }
    $Process.Refresh()
    if ($Process.HasExited) { return "pid=$($Process.Id) process=exited exitCode=$($Process.ExitCode)" }
    "pid=$($Process.Id) process=running"
}

function Wait-AcceptanceProcess([Diagnostics.Process]$Process, [string]$Phase, [int]$TimeoutSeconds,
    [Diagnostics.Stopwatch]$Timer) {
    $remaining = [Math]::Max(0, ($TimeoutSeconds * 1000) - $Timer.ElapsedMilliseconds)
    if (-not $Process.WaitForExit([int]$remaining)) {
        Stop-Acceptance 'TIMEOUT' $Phase $Timer $TimeoutSeconds (Get-AcceptanceProcessState $Process)
    }
    if ($Process.ExitCode -ne 0) {
        Stop-Acceptance 'FAIL' $Phase $Timer $TimeoutSeconds (Get-AcceptanceProcessState $Process)
    }
    Write-AcceptanceEvent 'PASS' $Phase $Timer $TimeoutSeconds (Get-AcceptanceProcessState $Process)
}

function Wait-AcceptanceProbe([string]$Phase, [int]$TimeoutSeconds, [scriptblock]$Check, [scriptblock]$DescribeState,
    [Diagnostics.Stopwatch]$Timer = [Diagnostics.Stopwatch]::StartNew()) {
    $limitMs = $TimeoutSeconds * 1000
    do {
        $result = & $Check
        $remaining = $limitMs - $Timer.ElapsedMilliseconds
        if ($result -and $remaining -ge 0) {
            Write-AcceptanceEvent 'PASS' $Phase $Timer $TimeoutSeconds (& $DescribeState)
            return $result
        }
        if ($remaining -gt 0) { Start-Sleep -Milliseconds ([int][Math]::Min(150, $remaining)) }
    } while ($Timer.ElapsedMilliseconds -lt $limitMs)
    Stop-Acceptance 'TIMEOUT' $Phase $Timer $TimeoutSeconds (& $DescribeState)
}

function Stop-AcceptanceProcess([Diagnostics.Process]$Process, [string]$Phase, [int]$TimeoutSeconds) {
    if (-not $Process) { return }
    $timer = [Diagnostics.Stopwatch]::StartNew()
    try {
        if (-not $Process.HasExited) { $Process.Kill() }
        if (-not $Process.WaitForExit($TimeoutSeconds * 1000)) {
            Write-AcceptanceEvent 'TIMEOUT' $Phase $timer $TimeoutSeconds (Get-AcceptanceProcessState $Process)
        }
    }
    catch {
        Write-AcceptanceEvent 'FAIL' $Phase $timer $TimeoutSeconds "exceptionType=$($_.Exception.GetType().Name)"
    }
    finally { $Process.Dispose() }
}

function Assert-AcceptanceSidecar([Diagnostics.Process]$Process, [Diagnostics.Stopwatch]$Timer) {
    if (-not $Process -or $Process.HasExited) {
        Stop-Acceptance 'FAIL' 'sidecar-health' $Timer 0 (Get-AcceptanceProcessState $Process)
    }
}
