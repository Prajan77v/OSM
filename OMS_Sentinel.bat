@echo off
title OMS Sentinel v9.0 Autonomous Surveillance System
color 0A
cd /d "%~dp0"

echo ===============================================================================
echo            OMS  --  OBJECT MONITORING SYSTEM  v9.0  LAUNCHER
echo                    AUTONOMOUS AI SURVEILLANCE SUPERCOMPUTER
echo ===============================================================================
echo.
echo [✦] Checking Environment...

if not exist "%~dp0python_env\python.exe" (
    echo [x] ERROR: Python environment not found in %~dp0python_env
    echo     Please ensure python_env is installed in the project root directory.
    pause
    exit /b 1
)

"%~dp0python_env\python.exe" -c "import insightface" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [✦] Installing InsightFace Face Recognition Engine ...
    "%~dp0python_env\python.exe" -m pip install insightface onnxruntime --quiet
)

echo [✦] Cleaning up any previous background instances...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo [✦] Launching Web Dashboard in default browser...
start "" "http://localhost:8000"

echo [✦] Starting OMS Sentinel Engine on http://localhost:8000 ...
echo [✦] Press Ctrl+C in this window to stop the system.
echo.

"%~dp0python_env\python.exe" main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [x] OMS Sentinel stopped with error code %ERRORLEVEL%.
)

pause
