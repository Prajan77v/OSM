@echo off
setlocal enabledelayedexpansion
:: OMS Sentinel - Camera Access Fix
:: Run this as Administrator

echo ================================================
echo   OMS Sentinel - Camera Access Fix
echo ================================================
echo.

:: Check for admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Must run as Administrator!
    echo Right-click and choose "Run as administrator"
    pause
    exit /b 1
)

echo [1/5] System-level camera access...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam" /v "Value" /t REG_SZ /d "Allow" /f
echo Done.

echo [2/5] User-level camera access...
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam" /v "Value" /t REG_SZ /d "Allow" /f
echo Done.

echo [3/5] Non-packaged (desktop) apps camera access...
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam\NonPackaged" /v "Value" /t REG_SZ /d "Allow" /f
echo Done.

echo [4/5] Removing WdmCompanionFilter block...
powershell -Command "Remove-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Enum\USB\VID_30C9^&PID_00A6\01.00.00\Device Parameters' -Name 'LowerFilters' -Force -ErrorAction SilentlyContinue; Write-Host 'Filter removed (or was not present).'"
echo Done.

echo [5/5] Restarting FrameServer...
net stop FrameServer >nul 2>&1
net start FrameServer >nul 2>&1
echo Done.

echo.
echo ================================================
echo   DONE! Please RESTART your PC now.
echo ================================================
echo.
set /p RESTART=Restart now? (Y/N): 
if /i "!RESTART!"=="Y" shutdown /r /t 5 /c "OMS Camera Fix"
pause
