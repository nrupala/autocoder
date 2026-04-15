@echo off
REM AutoCoder Setup Script for Windows
REM =================================

echo =====================================
echo AutoCoder Setup
echo =====================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10 or higher.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated

REM Install requirements
echo.
echo Installing dependencies...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM Install dev dependencies
echo.
echo Installing dev dependencies...
pip install pytest pytest-cov mypy ruff >nul 2>&1
echo [OK] Dev dependencies installed

REM Check Ollama
echo.
echo Checking Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama not found. Install from https://ollama.ai
) else (
    echo [OK] Ollama found
)

REM Create necessary directories
echo.
echo Creating directories...
if not exist ".autocoder" mkdir .autocoder
if not exist ".autocoder\keys" mkdir .autocoder\keys
if not exist "memory" mkdir memory
echo [OK] Directories created

REM Run tests
echo.
echo Running tests...
pytest tests/ -v --tb=short
if errorlevel 1 (
    echo [WARNING] Some tests failed
) else (
    echo [OK] All tests passed
)

echo.
echo =====================================
echo Setup Complete!
echo =====================================
echo.
echo To activate the environment:
echo   venv\Scripts\activate
echo.
echo To run AutoCoder:
echo   python cli.py "your request"
echo   or
echo   autocoder "your request"
echo.
pause
