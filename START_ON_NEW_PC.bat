@echo off
title OMS Sentinel - Automatic Setup & Launcher for New PC
cd /d "%~dp0"
cls
echo ==============================================================================
echo           OMS SENTINEL v9.0 -- FRESH PC AUTOMATIC LAUNCH PROTOCOL
echo ==============================================================================
echo.

:: 1. Check if Microsoft Visual C++ 2015-2022 x64 is installed
echo [1/3] Checking Microsoft Visual C++ Runtimes...
if not exist "%SystemRoot%\System32\vcruntime140.dll" (
    echo.
    echo [!] Microsoft Visual C++ Runtime missing on this clean PC.
    echo [*] Installing bundled Microsoft Visual C++ Runtime (vc_redist.x64.exe)...
    if exist "vc_redist.x64.exe" (
        start /wait "" "vc_redist.x64.exe" /passive /norestart
        echo [OK] Runtime installed successfully!
    )
) else (
    echo [OK] Visual C++ Runtime detected.
)

echo.
echo [2/3] Opening Web Matrix Interface (http://localhost:8000)...
start "" "http://localhost:8000"

echo.
echo [3/3] Starting OMS AI Surveillance Engine (15 Camera Channels)...
echo ==============================================================================
echo.

if exist "OMS_Sentinel.exe" (
    OMS_Sentinel.exe
) else (
    echo [!] OMS_Sentinel.exe not found in this folder.
)

echo.
echo ==============================================================================
echo [!] Process exited. (Keeping window open for review)
pause
