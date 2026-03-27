@echo off
REM ============================================================================
REM PALLAVI QA AUTOMATION - Single-Command Test Runner
REM ============================================================================
REM
REM Usage:
REM   qa_run_all.bat              - Run using Python (preferred, cross-platform)
REM   qa_run_all.bat --powershell - Run using PowerShell (Windows-native)
REM
REM ============================================================================

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ============================================================================
echo PALLAVI E2E QA TEST SUITE
echo ============================================================================
echo.

REM Check if backend is running
echo Checking backend connectivity...
timeout /t 1 /nobreak > nul

powershell -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop; exit 0 } catch { exit 1 }" >nul 2>&1

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Backend is not responding at http://127.0.0.1:8000
    echo.
    echo Please start the backend first:
    echo   uvicorn app.main:app --host 127.0.0.1 --port 8000
    echo.
    exit /b 1
)

echo [OK] Backend is responsive
echo.

REM Determine which script to run
if "%1"=="--powershell" (
    echo Running QA suite using PowerShell...
    echo.
    powershell -ExecutionPolicy Bypass -File qa_run.ps1
    set QA_EXIT=!ERRORLEVEL!
) else (
    REM Use Python by default
    python --version > nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python not found. Please install Python or run with --powershell flag
        exit /b 1
    )
    
    echo Running QA suite using Python...
    echo.
    python qa_run.py
    set QA_EXIT=!ERRORLEVEL!
)

echo.
echo ============================================================================
if %QA_EXIT% equ 0 (
    echo ✓ QA TEST SUITE COMPLETED SUCCESSFULLY
) else (
    echo ✗ QA TEST SUITE COMPLETED WITH FAILURES
)
echo ============================================================================
echo.

REM Display report files if they exist
if exist qa_report.txt (
    echo Generated Report: qa_report.txt
)
if exist qa_report_python.json (
    echo Generated Report: qa_report_python.json
)

exit /b %QA_EXIT%
