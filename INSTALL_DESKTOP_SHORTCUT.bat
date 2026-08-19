@echo off
title OMS Sentinel Shortcut Installer
cd /d "%~dp0"
cls
echo ==============================================================================
echo          CREATING DESKTOP PROTOCOL SHORTCUT FOR OMS SENTINEL
echo ==============================================================================
set "TARGET_BAT=%~dp01_CLICK_RUN.bat"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\OMS Sentinel.lnk'); $s.TargetPath = '%TARGET_BAT%'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = 'shell32.dll,220'; $s.Save()"
echo.
echo [OK] Shortcut created on your Desktop: "OMS Sentinel"
echo Double-click that desktop icon anytime to run OMS Sentinel instantly in 1 second!
echo.
pause
