@echo off
REM ============================================================================
REM PALLAVI: START ALL SYSTEMS (ONE CLICK)
REM ============================================================================
REM Starts everything except ngrok:
REM - Ollama (if installed)
REM - Backend (FastAPI)
REM - Frontend (Vite React)
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo PALLAVI: ONE-CLICK FULL STARTUP
echo ============================================================================
echo.

REM Check prerequisites
echo [1/6] Checking prerequisites...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    exit /b 1
)
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found
    exit /b 1
)
echo [OK] Python available
echo [OK] Node.js available
echo.

REM Cleanup backend port
echo [2/6] Cleaning backend port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM Cleanup frontend port
echo [3/6] Cleaning frontend port 5173...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173"') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM Optional: start Ollama if installed and not already running
echo [4/6] Checking Ollama service (port 11434)...
set "OLLAMA_PORT_IN_USE="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":11434" ^| findstr "LISTENING"') do (
    set "OLLAMA_PORT_IN_USE=1"
)

if defined OLLAMA_PORT_IN_USE (
    echo [OK] Ollama already running on 127.0.0.1:11434, skipping start
) else (
    where ollama >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Ollama not found in PATH, skipping Ollama startup
    ) else (
        start "PALLAVI Ollama" cmd /k ollama serve
        timeout /t 2 /nobreak >nul
        echo [OK] Ollama start command sent
    )
)
echo.

REM Ensure frontend dependencies
echo [5/6] Checking frontend dependencies...
if not exist "%cd%\analytics-ui\node_modules" (
    echo [INFO] node_modules missing, running npm install...
    pushd "%cd%\analytics-ui"
    call npm install
    popd
) else (
    echo [OK] Frontend dependencies present
)
echo.

REM Start backend and frontend
echo [6/6] Starting backend and frontend...
start "PALLAVI Backend" /D "%cd%" cmd /k set SLA_MONITOR_ENABLED=false ^&^& python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
timeout /t 3 /nobreak >nul
start "PALLAVI Frontend" /D "%cd%\analytics-ui" cmd /k npm run dev

echo.
echo ============================================================================
echo ALL SYSTEMS STARTED (except ngrok)
echo ============================================================================
echo Backend:   http://127.0.0.1:8000
echo Health:    http://127.0.0.1:8000/health
echo Frontend:  http://127.0.0.1:5173
echo Admin UI:  http://127.0.0.1:5173/admin
echo.
echo NOTE: Keep ngrok running separately.
echo       If ngrok URL changed, update BASE_URL in .env.
echo       SLA monitor is forced OFF in this launcher.
echo.
exit /b 0
