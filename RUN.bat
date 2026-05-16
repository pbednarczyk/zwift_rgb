@echo off
REM ============================================
REM Zwift RGB - Start Script
REM ============================================
cls
echo.
echo  🚴 Zwift RGB Control - Starting...
echo.

REM Navigate to project directory
cd /d "%~dp0"

REM Activate virtual environment and run the app
call .venv\Scripts\activate.bat
python -m app.main

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo  ❌ Error occurred. Press any key to close...
    pause
)
