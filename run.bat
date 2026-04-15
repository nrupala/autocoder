@echo off
REM AutoCoder Launcher Script for Windows
REM ===============================

echo Starting AutoCoder...

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Check and install dependencies
if not exist "requirements.txt" (
    echo Error: requirements.txt not found
    pause
    exit /b 1
)

REM Run AutoCoder
if "%~1"=="" (
    python -m cli --help
) else (
    python -m cli %*
)

pause
