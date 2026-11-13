param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [switch]$RequireOffline
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
        $value = & $Probe
        if ($value) { return $value }
        Start-Sleep -Milliseconds 150
    } while ($timer.Elapsed.TotalSeconds -lt 30)
    throw "Timed out waiting for $Description."
}

function Find-Control($Window, $Property, [string]$Value) {
    $condition = New-Object Windows.Automation.PropertyCondition($Property, $Value)
    Wait-For $Value {
        # Enumerating the tree also initializes the WebView2 accessibility provider.
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
    [Diagnostics.Process]::Start($start)
}

function Get-DashboardWindow($Process) {
    Wait-For 'the Tauri window' {
        $Process.Refresh()
        if ($Process.HasExited) { throw "Desktop exited with code $($Process.ExitCode)." }
        if ($Process.MainWindowHandle -ne [IntPtr]::Zero) {
            [Windows.Automation.AutomationElement]::FromHandle($Process.MainWindowHandle)
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

$temp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
$runRoot = Join-Path $temp ('rigarus-tauri-smoke-' + [Guid]::NewGuid().ToString('N'))
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
    Close-Dashboard $process
    if (Get-Process -Id $firstSidecar.ProcessId -ErrorAction SilentlyContinue) {
        throw 'The sidecar remained running after closing the Tauri window.'
    }
    $process.Dispose()

    $process = Start-Dashboard
    $window = Get-DashboardWindow $process
    $note = (Find-Control $window $automationId 'demo-note').GetCurrentPattern($valuePattern)
    if ($note.Current.Value -ne $newNote) { throw 'Saved note did not survive a desktop restart.' }
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
