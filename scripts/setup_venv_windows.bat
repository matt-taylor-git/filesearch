@echo off
REM Compatibility wrapper for the canonical uv development setup.

echo Setting up File Search development environment...

where uv >nul 2>&1
if errorlevel 1 (
    echo Error: uv is required. See https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

uv sync --locked
if errorlevel 1 exit /b 1

uv run pre-commit install
if errorlevel 1 exit /b 1

echo.
echo [OK] Development environment setup complete!
echo.
echo To run the application:
echo   uv run python -m filesearch
echo.
echo To run tests:
echo   uv run pytest
echo.
echo To format code:
echo   uv run ruff format .
echo.
echo To lint code:
echo   uv run ruff check .
