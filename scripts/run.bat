@echo off
REM Run File Search from source (Windows)
REM Creates a local venv and installs runtime deps if missing.
REM Usage: scripts\run.bat [--debug] [other options]

setlocal EnableExtensions EnableDelayedExpansion

REM Always run from the repository root (parent of scripts/)
cd /d "%~dp0.."

set "VENV_DIR="
if exist "venv\Scripts\python.exe" (
    set "VENV_DIR=venv"
) else if exist ".venv\Scripts\python.exe" (
    set "VENV_DIR=.venv"
)

if not defined VENV_DIR (
    echo No virtual environment found. Setting one up...
    echo.

    where python >nul 2>&1
    if errorlevel 1 (
        echo Error: Python is not installed or not in PATH.
        echo Install Python 3.9+ and try again.
        exit /b 1
    )

    for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set python_version=%%i
    for /f "tokens=1,2 delims=." %%a in ("!python_version!") do (
        set major=%%a
        set minor=%%b
    )

    if !major! LSS 3 (
        echo Error: Python 3.9 or higher is required. Found: !python_version!
        exit /b 1
    )
    if !major! EQU 3 if !minor! LSS 9 (
        echo Error: Python 3.9 or higher is required. Found: !python_version!
        exit /b 1
    )

    echo [OK] Python !python_version! detected
    echo Creating virtual environment in .\venv ...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment.
        exit /b 1
    )

    set "VENV_DIR=venv"

    echo Upgrading pip...
    "venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 (
        echo Error: Failed to upgrade pip.
        exit /b 1
    )

    echo Installing runtime dependencies...
    "venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install requirements.txt.
        exit /b 1
    )

    echo Installing File Search package ^(editable^)...
    "venv\Scripts\python.exe" -m pip install -e .
    if errorlevel 1 (
        echo Error: Failed to install the local package.
        exit /b 1
    )

    echo.
    echo [OK] Virtual environment ready.
    echo.
)

set "PYTHON_EXE=!VENV_DIR!\Scripts\python.exe"

REM Ensure the package is importable even if editable install is incomplete
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

"%PYTHON_EXE%" -m filesearch %*
exit /b %ERRORLEVEL%
