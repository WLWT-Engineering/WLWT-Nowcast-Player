# ============================================================
#  setup-autostart.ps1
#  Registers the Python Nowcast player to start automatically at
#  logon, running HIDDEN (via pythonw.exe). Finds pythonw by full
#  path so it works even when run from an elevated (admin) window
#  where your per-user Python isn't on PATH.
#
#  Run (in an ADMIN PowerShell, from this folder):
#     powershell -ExecutionPolicy Bypass -File .\setup-autostart.ps1
#
#  If it still can't find pythonw, pass the path yourself:
#     powershell -ExecutionPolicy Bypass -File .\setup-autostart.ps1 -PythonwPath "C:\full\path\to\pythonw.exe"
# ============================================================

param([string]$PythonwPath = "")

$TaskName  = "WLWT Nowcast Player"
$ScriptDir = $PSScriptRoot
$Script    = Join-Path $ScriptDir "wlwt_autoplay.py"

if (-not (Test-Path $Script)) {
    Write-Error "wlwt_autoplay.py not found next to this script."; exit 1
}

function Find-Pythonw {
    if ($PythonwPath -and (Test-Path $PythonwPath)) { return $PythonwPath }

    $c = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
    if ($c) { return $c }

    $py = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
    if ($py) {
        $p = Join-Path (Split-Path $py) "pythonw.exe"
        if (Test-Path $p) { return $p }
    }

    # Search common install locations, including per-user installs under any
    # user profile (this fixes the "admin can't see user PATH" case).
    $globs = @(
        "$env:LOCALAPPDATA\Programs\Python\Python3*\pythonw.exe",
        "$env:ProgramFiles\Python3*\pythonw.exe",
        "${env:ProgramFiles(x86)}\Python3*\pythonw.exe",
        "C:\Python3*\pythonw.exe",
        "C:\Users\*\AppData\Local\Programs\Python\Python3*\pythonw.exe"
    )
    foreach ($g in $globs) {
        $hit = Get-ChildItem $g -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }
    return $null
}

$pyw = Find-Pythonw
if (-not $pyw) {
    Write-Error "pythonw.exe not found. Re-run with the full path, e.g.:`n  powershell -ExecutionPolicy Bypass -File .\setup-autostart.ps1 -PythonwPath `"C:\full\path\to\pythonw.exe`""
    exit 1
}
Write-Host "Using pythonw: $pyw"

$action  = New-ScheduledTaskAction -Execute $pyw -Argument "`"$Script`"" -WorkingDirectory $ScriptDir
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Force

Write-Host "Registered '$TaskName' to start at logon (hidden), using the path above."
Write-Host "Start it now:  Start-ScheduledTask -TaskName `"$TaskName`""
