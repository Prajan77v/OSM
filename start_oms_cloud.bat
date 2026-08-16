@echo off
title OMS Cloud API Server (Local Testing)
cls
echo ===============================================================================
echo            OMS  --  OBJECT MONITORING SYSTEM  v9.0  CLOUD API
echo                     LIGHTWEIGHT FASTAPI CLOUD HUB
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

echo [*] Starting OMS Cloud API on port 8000...
echo [*] Interactive Swagger Docs: http://localhost:8000/docs
echo.

"%PY_EXE%" cloud_api.py

pause
