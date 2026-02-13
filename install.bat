@echo off
REM ──────────────────────────────────────────────────────────
REM  ResumeFlow — one-command installer for Windows
REM ──────────────────────────────────────────────────────────

echo.
echo  ╔══════════════════════════════════════╗
echo  ║        ResumeFlow Installer          ║
echo  ╚══════════════════════════════════════╝
echo.

REM --- Check Python -------------------------------------------------------
echo [INFO]  Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL]  Python 3.11+ is required but not found.
    echo         Download it from https://python.org
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PY_VERSION=%%i
echo [OK]    Python %PY_VERSION% found

REM --- Create virtual environment -----------------------------------------
if not exist ".venv" (
    echo [INFO]  Creating virtual environment...
    python -m venv .venv
    echo [OK]    Virtual environment created
) else (
    echo [OK]    Virtual environment already exists
)

REM --- Install dependencies -----------------------------------------------
echo [INFO]  Installing ResumeFlow and dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet 2>nul
python -m pip install -e . --quiet
if errorlevel 1 (
    echo [FAIL]  Failed to install dependencies.
    echo         Try running manually:
    echo           .venv\Scripts\python.exe -m pip install -e .
    pause
    exit /b 1
)
echo [OK]    Dependencies installed

echo.
echo  ╔══════════════════════════════════════╗
echo  ║      Installation complete!          ║
echo  ╚══════════════════════════════════════╝
echo.
echo   To run ResumeFlow:
echo.
echo     .venv\Scripts\activate.bat
echo     resumeflow
echo.
echo   Or simply:
echo.
echo     .venv\Scripts\resumeflow.exe
echo.
pause
