@echo off
title OMS Sentinel - Autonomous AI Engine (RTX 4060)
cls
echo ===============================================================================
echo            OMS  --  OBJECT MONITORING SYSTEM  v9.0  AI ENGINE
echo                  AUTONOMOUS CUDA AI SURVEILLANCE NODE
echo ===============================================================================
echo.

cd /d "%~dp0"

:: Check virtual environment
if exist "python_env\Scripts\python.exe" (
    set "PY_EXE=python_env\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PY_EXE=venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

echo [i] Python Interpreter: %PY_EXE%
echo [i] Verifying CUDA GPU Acceleration...
"%PY_EXE%" -c "import torch; print('[+] GPU Device: ' + torch.cuda.get_device_name(0) if torch.cuda.is_available() else '[-] WARNING: CUDA NOT FOUND, RUNNING ON CPU')"

echo.
echo [*] Starting Local OMS AI Engine...
echo [*] Local Dashboard: http://localhost:8000
echo.

"%PY_EXE%" main.py

pause
