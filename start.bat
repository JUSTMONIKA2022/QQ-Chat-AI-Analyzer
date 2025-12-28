@echo off
setlocal
:: Ensure we use standard ASCII/ANSI compatible mode initially
:: Try to switch to UTF-8 for Chinese support, but silence output to avoid confusion
chcp 65001 >nul 2>&1

title QQ Chat AI Analyzer - Launcher

echo ========================================================
echo        QQ Chat AI Analyzer - Start Script
echo ========================================================

:: 1. Check Python
echo [1/3] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

:: 2. Install Dependencies
echo [2/3] Checking dependencies...
if exist "requirements.txt" (
    echo Installing/Updating libraries...
    :: Use 'python -m pip' instead of 'pip' to avoid PATH issues
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to install dependencies.
        echo Please check your internet connection or python installation.
        pause
        exit /b
    )
) else (
    echo [ERROR] requirements.txt not found.
    pause
    exit /b
)

:: 3. Start App
echo [3/3] Starting Application...
echo.
echo     Please visit: http://127.0.0.1:5000
echo.

:: Start browser
start "" /b cmd /c "timeout /t 3 >nul && start http://127.0.0.1:5000"

:: Run Flask App
python app.py

pause
