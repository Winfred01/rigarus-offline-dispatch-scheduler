param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [switch]$RequireOffline,
    [switch]$IncludeProjects
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$Executable = (Resolve-Path -LiteralPath $Executable).Path

if ($RequireOffline -and [System.Net.NetworkInformation.NetworkInterface]::GetIsNetworkAvailable()) {
    throw 'An active network adapter is present. Disconnect from the network and rerun.'
}

function Wait-For([scriptblock]$Probe, [string]$Description) {
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    do {
        $value = & $Probe
        if ($value) {
            return $value
        }

        Start-Sleep -Milliseconds 200
    } while ($timer.Elapsed.TotalSeconds -lt 30)

    throw "Timed out waiting for $Description."
}

function Start-Demo {
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $Executable
    $startInfo.WorkingDirectory = Split-Path -Parent $Executable
    $startInfo.UseShellExecute = $false
    $startInfo.EnvironmentVariables['RIGARUS_SMOKE_DATA_ROOT'] = $root
    return [System.Diagnostics.Process]::Start($startInfo)
}

function Get-DemoWindow([System.Diagnostics.Process]$Process) {
    Wait-For -Description 'the WPF main window' -Probe {
        $Process.Refresh()
        if ($Process.HasExited) {
            throw "The app exited with code $($Process.ExitCode) before displaying its window."
        }
        if ($Process.MainWindowHandle -ne [IntPtr]::Zero) {
            [System.Windows.Automation.AutomationElement]::FromHandle($Process.MainWindowHandle)
        }
    }
}

function Get-Control($Window, [string]$Id) {
    $propertyCondition = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::AutomationIdProperty, $Id
    )
    Wait-For -Description $Id -Probe {
        $Window.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $propertyCondition)
    }
}

function Close-Demo($Window, [System.Diagnostics.Process]$Process) {
    $pattern = $Window.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern)
    $pattern.Close()
    if (-not $Process.WaitForExit(10000) -or $Process.ExitCode -ne 0) {
        throw 'The app did not close cleanly.'
    }
}

if ($IncludeProjects) {
    . (Join-Path $PSScriptRoot 'ProjectMasterSmoke.ps1')
}

$root = Join-Path ([System.IO.Path]::GetTempPath()) ('rigarus-m0-smoke-' + [guid]::NewGuid().ToString('N'))
$process = $null
try {
    $process = Start-Demo
    $window = Get-DemoWindow $process
    if ($window.Current.Name -ne 'Rigarus Offline Dispatch Scheduler') {
        throw 'Unexpected main window title.'
    }
    if ((Get-Control $window 'DemoMode').Current.Name -ne 'Demo Mode') {
        throw 'Demo Mode is missing.'
    }
    $projectLabel = (Get-Control $window 'ProjectLabel').Current.Name
    if ($projectLabel -notlike 'DEMO-001*Example Site') {
        throw 'The synthetic project did not load.'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $root 'data/rigarus.db'))) {
        throw 'The isolated database was not created.'
    }

    $note = Get-Control $window 'DemoNote'
    $value = $note.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
    if ($value.Current.Value -ne 'Synthetic sample for M0.') {
        throw 'The initial synthetic note did not load.'
    }

    $newNote = 'Saved and reopened in M0 smoke test.'
    $value.SetValue($newNote)
    $save = Get-Control $window 'SaveNote'
    $save.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    $status = Get-Control $window 'DemoStatus'
    Wait-For -Description 'the save confirmation' -Probe { $status.Current.Name -eq 'Saved locally.' } | Out-Null
    Close-Demo $window $process
    $process.Dispose()
    $process = $null

    $process = Start-Demo
    $window = Get-DemoWindow $process
    $note = Get-Control $window 'DemoNote'
    $value = $note.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
    if ($value.Current.Value -ne $newNote) {
        throw 'The saved note was missing after restarting.'
    }
    if ($IncludeProjects) {
        Test-ProjectMaster $window $process
        Close-Demo $window $process
        $process.Dispose()
        $process = $null

        $process = Start-Demo
        $window = Get-DemoWindow $process
        $note = Get-Control $window 'DemoNote'
        if ($note.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -ne $newNote) {
            throw 'Project Master changes did not preserve the demo note.'
        }
        Test-ProjectMasterAfterRestart $window
    }
    Close-Demo $window $process
    Write-Host 'PASS: WPF launched, migrated SQLite, loaded the fixture, and retained the saved note after restart.'
    if ($RequireOffline) {
        Write-Host 'PASS: Windows reported no active network adapter before launch.'
    }
}
finally {
    if ($null -ne $process) {
        if (-not $process.HasExited) {
            $process.Kill()
            $process.WaitForExit()
        }
        $process.Dispose()
    }

    # The GUID path is created for this run and must stay in the temp directory.
    $temp = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    $resolved = [System.IO.Path]::GetFullPath($root)
    if ($resolved.StartsWith($temp + 'rigarus-m0-smoke-', [System.StringComparison]::OrdinalIgnoreCase) -and
        (Test-Path -LiteralPath $resolved -PathType Container)) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
