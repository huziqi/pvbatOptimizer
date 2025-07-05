@echo off
echo ===============================================
echo PV Battery Optimizer Web Application
echo ===============================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Activate virtual environment
echo Activating virtual environment...
call conda activate ecogrid
if %errorlevel% neq 0 (
    echo Warning: Failed to activate ecogrid environment
    echo Continuing with current environment...
)

:: Run the application
echo Starting web application...
python run_web_app.py

pause 