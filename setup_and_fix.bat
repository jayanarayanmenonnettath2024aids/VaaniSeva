@echo off
setlocal enabledelayedexpansion

REM ================================================
REM PALLAVI Self-Healing Setup Script (Windows)
REM Checks and fixes prerequisites where possible.
REM ================================================

set "CRITICAL_FAILED=0"
set "PARTIAL_WARNING=0"

echo.
echo ================================================
echo      PALLAVI SETUP AND FIX (SELF-HEALING)
echo ================================================
echo.

REM Always run from project root (script location)
cd /d "%~dp0"

REM --------------------------------
REM STEP 1 - PYTHON CHECK
REM --------------------------------
echo [STEP 1/10] Checking Python...
python --version >nul 2>&1
if %errorlevel%==0 (
    echo [PASS] Python detected
) else (
    echo [ERROR] Python not found
    echo [ACTION] Please install Python from https://www.python.org/downloads/
    set "CRITICAL_FAILED=1"
)

if "%CRITICAL_FAILED%"=="1" goto :FINAL

echo.

REM --------------------------------
REM STEP 2 - NODE + NPM CHECK
REM --------------------------------
echo [STEP 2/10] Checking Node.js and npm...
node -v >nul 2>&1
if %errorlevel%==0 (
    echo [PASS] Node.js detected
) else (
    echo [ERROR] Node.js not found
    echo [ACTION] Please install Node.js LTS from https://nodejs.org/
    set "CRITICAL_FAILED=1"
)

npm -v >nul 2>&1
if %errorlevel%==0 (
    echo [PASS] npm detected
) else (
    echo [ERROR] npm not found
    echo [ACTION] Reinstall Node.js LTS (npm is bundled)
    set "CRITICAL_FAILED=1"
)

if "%CRITICAL_FAILED%"=="1" goto :FINAL

echo.

REM --------------------------------
REM STEP 3 - NGROK CHECK
REM --------------------------------
echo [STEP 3/10] Checking ngrok...
ngrok version >nul 2>&1
if %errorlevel%==0 (
    echo [PASS] ngrok detected
) else (
    echo [WARNING] ngrok not installed
    echo [ACTION] Download from https://ngrok.com/download
    set "PARTIAL_WARNING=1"
)

echo.

REM --------------------------------
REM STEP 4 - OLLAMA CHECK
REM --------------------------------
echo [STEP 4/10] Checking Ollama...
ollama --version >nul 2>&1
if %errorlevel%==0 (
    echo [PASS] Ollama detected
) else (
    echo [ERROR] Ollama not installed
    echo [ACTION] Install from https://ollama.com/download
    set "CRITICAL_FAILED=1"
)

if "%CRITICAL_FAILED%"=="1" goto :FINAL

echo.

REM --------------------------------
REM STEP 5 - OLLAMA MODEL CHECK / DOWNLOAD
REM --------------------------------
echo [STEP 5/10] Verifying Ollama model phi3:mini...
set "MODEL_FOUND=0"
ollama list > "%TEMP%\pallavi_ollama_list.txt" 2>nul
if %errorlevel%==0 (
    findstr /I /C:"phi3:mini" "%TEMP%\pallavi_ollama_list.txt" >nul 2>&1
    if !errorlevel!==0 (
        set "MODEL_FOUND=1"
        echo [PASS] Model phi3:mini is available
    ) else (
        echo [ACTION] Downloading phi3:mini model...
        ollama pull phi3:mini
        if !errorlevel!==0 (
            echo [PASS] Model phi3:mini downloaded successfully
        ) else (
            echo [ERROR] Failed to download phi3:mini
            echo [ACTION] Run manually: ollama pull phi3:mini
            set "CRITICAL_FAILED=1"
        )
    )
) else (
    echo [ERROR] Unable to run 'ollama list'
    echo [ACTION] Verify Ollama installation and permissions
    set "CRITICAL_FAILED=1"
)

del "%TEMP%\pallavi_ollama_list.txt" >nul 2>&1
if "%CRITICAL_FAILED%"=="1" goto :FINAL

echo.

REM --------------------------------
REM STEP 6 - .ENV CHECK / CREATE
REM --------------------------------
echo [STEP 6/10] Checking .env file...
if exist ".env" (
    echo [PASS] .env exists
) else (
    if exist ".env.example" (
        echo [ACTION] Creating .env from template...
        copy /Y ".env.example" ".env" >nul
        if !errorlevel!==0 (
            echo [PASS] .env created from .env.example
        ) else (
            echo [ERROR] Failed to create .env from .env.example
            set "CRITICAL_FAILED=1"
        )
    ) else (
        echo [ERROR] .env and .env.example both missing
        echo [ACTION] Create .env.example first, then rerun script
        set "CRITICAL_FAILED=1"
    )
)

if "%CRITICAL_FAILED%"=="1" goto :FINAL

echo.

REM --------------------------------
REM STEP 7 - BACKEND DEPENDENCIES
REM --------------------------------
echo [STEP 7/10] Checking backend dependencies...
if exist "app\requirements.txt" (
    echo [ACTION] Installing backend dependencies from app\requirements.txt ...
    python -m pip install -r "app\requirements.txt"
    if !errorlevel!==0 (
        echo [WARNING] Backend dependency installation had issues
        echo [ACTION] Review pip output and fix package errors
        set "PARTIAL_WARNING=1"
    ) else (
        echo [PASS] Backend dependencies installed
    )
) else (
    echo [WARNING] app\requirements.txt not found, skipping backend install
    set "PARTIAL_WARNING=1"
)

echo.

REM --------------------------------
REM STEP 8 - FRONTEND DEPENDENCIES
REM --------------------------------
echo [STEP 8/10] Checking frontend dependencies...
if exist "analytics-ui\package.json" (
    echo [ACTION] Installing frontend dependencies from analytics-ui\package.json ...
    pushd "analytics-ui"
    npm install
    if !errorlevel!==0 (
        echo [WARNING] Frontend dependency installation had issues
        echo [ACTION] Review npm output and fix package errors
        set "PARTIAL_WARNING=1"
    ) else (
        echo [PASS] Frontend dependencies installed
    )
    popd
) else (
    echo [WARNING] analytics-ui\package.json not found, skipping frontend install
    set "PARTIAL_WARNING=1"
)

echo.

REM --------------------------------
REM STEP 9 - PORT CHECK
REM --------------------------------
echo [STEP 9/10] Checking ports 8000 and 5173...
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [WARNING] Port 8000 is already in use, but continuing...
    set "PARTIAL_WARNING=1"
) else (
    echo [PASS] Port 8000 is available
)

netstat -ano | findstr /R /C:":5173 .*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [WARNING] Port 5173 is already in use, but continuing...
    set "PARTIAL_WARNING=1"
) else (
    echo [PASS] Port 5173 is available
)

echo.

REM --------------------------------
REM STEP 10 - FINAL STATUS
REM --------------------------------
:FINAL
echo [STEP 10/10] Final status
echo.
if "%CRITICAL_FAILED%"=="0" (
    if "%PARTIAL_WARNING%"=="0" (
        echo [READY] System fully set up 🚀
    ) else (
        echo [PARTIAL] Some steps require manual fix
        echo [ACTION] Review [WARNING] messages above
    )
) else (
    echo [PARTIAL] Some steps require manual fix
    echo [ACTION] Review [ERROR] messages above
)

echo.
pause
endlocal
