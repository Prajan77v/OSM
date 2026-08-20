# OMS Edge Agent — Windows Service / Scheduled Task Auto-Start Installer
# Run in an elevated (Administrator) PowerShell window.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = (Get-Item "$ScriptDir\..\..").FullName
$PythonExe = "$RootDir\venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python.exe"
}

$TaskName = "OMSEdgeAgent"
$AgentScript = "$RootDir\edge\agent.py"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Installing OMS Edge Agent Windows Auto-Start Task  " -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "[i] Root Directory : $RootDir"
Write-Host "[i] Python Executable: $PythonExe"
Write-Host "[i] Target Script    : $AgentScript"

# Unregister existing task if present
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Define action and trigger (At startup + automatically restart on failure)
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$AgentScript`"" -WorkingDirectory $RootDir
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit 0

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -User "SYSTEM" -RunLevel Highest

Write-Host "`n[+] SUCCESS: OMS Edge Agent is registered to start automatically on Windows boot." -ForegroundColor Green
Write-Host "[*] To start it manually right now: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
