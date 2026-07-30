@echo off
REM Run File Search from source (Windows)
REM Synchronizes and runs through the canonical locked uv environment.
REM Usage: scripts\run.bat [--debug] [other options]

setlocal EnableExtensions

REM Always run from the repository root (parent of scripts/)
cd /d "%~dp0.."

where uv >nul 2>&1
if errorlevel 1 (
    echo Error: uv is required. See https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

uv run --locked python -m filesearch %*
exit /b %ERRORLEVEL%
