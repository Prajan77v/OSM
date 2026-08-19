@echo off
title OMS Sentinel v9.0 Matrix
cd /d "%~dp0"
cls
echo ==============================================================================
echo           OMS SENTINEL v9.0 -- 1-CLICK INSTANT LAUNCH PROTOCOL
echo ==============================================================================
echo.
echo [1/2] Opening Web Matrix Dashboard (http://localhost:8000)...
start "" "http://localhost:8000"
echo [2/2] Initializing Neural Vision Engine (15 Channels Online)...
echo.
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Process terminated with exit code %ERRORLEVEL%.
    pause
)
