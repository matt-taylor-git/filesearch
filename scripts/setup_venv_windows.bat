@echo off
REM Virtual environment setup script for Windows

echo Setting up File Search development environment...

REM Check if Python 3.9+ is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check Python version
for /f "tokens=2 delims= " %%i in ('python --version') do set python_version=%%i
for /f "tokens=1,2 delims=." %%a in ("%python_version%") do (
    set major=%%a
    set minor=%%b
)

if %major% LSS 3 (
    echo Error: Python 3.9 or higher is required. Found: %python_version%
    exit /b 1
)

if %major% EQU 3 (
    if %minor% LSS 9 (
        echo Error: Python 3.9 or higher is required. Found: %python_version%
        exit /b 1
    )
)

echo [OK] Python %python_version% detected

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
pip install --upgrade pip

REM Install runtime dependencies
echo Installing runtime dependencies...
pip install -r requirements.txt

REM Install development dependencies
echo Installing development dependencies...
pip install -r requirements-dev.txt

REM Install pre-commit hooks
echo Installing pre-commit hooks...
pre-commit install

echo.
echo [OK] Development environment setup complete!
echo.
echo To activate the virtual environment in future sessions:
echo   call venv\Scripts\activate.bat
echo.
echo To run the application:
echo   python -m filesearch
echo.
echo To run tests:
echo   pytest
echo.
echo To format code:
echo   black src tests
echo.
echo To lint code:
echo   flake8 src tests
