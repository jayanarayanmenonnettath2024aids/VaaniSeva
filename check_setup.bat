@echo off
setlocal enabledelayedexpansion

REM ==========================================
REM PALLAVI Setup Readiness Checker (Windows)
REM This script ONLY checks prerequisites.
REM It does NOT start any service.
REM ==========================================

set "HAS_ERROR=0"
set "HAS_WARNING=0"

echo.
echo ==========================================
echo        PALLAVI PRE-RUN READINESS CHECK
echo ==========================================
echo.

REM Run checks from the script directory
cd /d "%~dp0"

REM ------------------------------------------
REM 1) Python check
REM ------------------------------------------
python --version >nul 2>&1
if %errorlevel%==0 (
    echo [PASS] Python installed
) else (
    echo [ERROR] Python not installed
    echo        Fix: Install Python 3.x and add it to PATH.
    set "HAS_ERROR=1"
)

REM ------------------------------------------
REM 2) Node + npm check
REM ------------------------------------------
node -v >nul 2>&1
if %errorlevel%==0 (
    echo [PASS] Node.js installed
) else (
    echo [ERROR] Node.js not installed
    echo        Fix: Install Node.js LTS and add it to PATH.
    set "HAS_ERROR=1"
)

npm -v >nul 2>&1
if %errorlevel%==0 (
    echo [PASS] npm installed
) else (
    echo [ERROR] npm not installed
    echo        Fix: Reinstall Node.js LTS (npm is included).
    set "HAS_ERROR=1"
)

REM ------------------------------------------
REM 3) ngrok check
REM ------------------------------------------
ngrok version >nul 2>&1
if %errorlevel%==0 (
    echo [PASS] ngrok installed
) else (
    echo [FAIL] ngrok missing
    echo        Fix: Install ngrok and add it to PATH.
    set "HAS_ERROR=1"
)

REM ------------------------------------------
REM 4) Ollama binary check
REM ------------------------------------------
ollama --version >nul 2>&1
if %errorlevel%==0 (
    echo [PASS] Ollama installed
) else (
    echo [ERROR] Ollama not installed
    echo        Fix: Install Ollama from https://ollama.com/download
    set "HAS_ERROR=1"
)

REM ------------------------------------------
REM 5) Ollama model check (phi3:mini)
REM ------------------------------------------
set "MODEL_FOUND=0"
ollama list > "%TEMP%\pallavi_ollama_models.txt" 2>nul
if %errorlevel%==0 (
    findstr /I /C:"phi3:mini" "%TEMP%\pallavi_ollama_models.txt" >nul 2>&1
    if !errorlevel!==0 (
        set "MODEL_FOUND=1"
        echo [PASS] Ollama model phi3:mini available
    ) else (
        echo [WARNING] Ollama model phi3:mini not found
        echo          Fix: Run ^"ollama run phi3:mini^"
        set "HAS_WARNING=1"
    )
) else (
    echo [WARNING] Could not read ollama model list
    echo          Fix: Ensure Ollama is installed and accessible.
    set "HAS_WARNING=1"
)

del "%TEMP%\pallavi_ollama_models.txt" >nul 2>&1

REM ------------------------------------------
REM 6) Project structure check
REM ------------------------------------------
if exist "app\" (
    echo [PASS] app/ found
) else (
    echo [ERROR] Project structure incomplete: app/ missing
    set "HAS_ERROR=1"
)

if exist "analytics-ui\" (
    echo [PASS] analytics-ui/ found
) else (
    echo [ERROR] Project structure incomplete: analytics-ui/ missing
    set "HAS_ERROR=1"
)

REM ------------------------------------------
REM 7) .env check
REM ------------------------------------------
if exist ".env" (
    echo [PASS] .env file found
) else (
    echo [ERROR] .env file not found
    echo        Fix: Create .env from .env.example.
    set "HAS_ERROR=1"
)

REM ------------------------------------------
REM 8) Port checks
REM ------------------------------------------
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [WARNING] Port 8000 already in use
    echo          Fix: Stop the process using 8000 before starting backend.
    set "HAS_WARNING=1"
) else (
    echo [PASS] Port 8000 available
)

netstat -ano | findstr /R /C:":5173 .*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [WARNING] Port 5173 already in use
    echo          Fix: Stop the process using 5173 before starting frontend.
    set "HAS_WARNING=1"
) else (
    echo [PASS] Port 5173 available
)

REM ------------------------------------------
REM 9) Optional internet check
REM ------------------------------------------
ping -n 1 google.com >nul 2>&1
if %errorlevel%==0 (
    echo [PASS] Internet connectivity check passed
) else (
    echo [WARNING] No internet connectivity (Twilio may fail)
    set "HAS_WARNING=1"
)

echo.
echo ==========================================
if "%HAS_ERROR%"=="0" (
    if "%HAS_WARNING%"=="0" (
        echo [READY] System ready to run 🚀
    ) else (
        echo [READY] System mostly ready with warnings
        echo         Review warnings before running in production.
    )
) else (
    echo [NOT READY] Fix issues before running system
)
echo ==========================================
echo.

pause
endlocal
