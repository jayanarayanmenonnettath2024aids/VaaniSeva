@echo off
REM ===========================================================================
REM PALLAVI DEMO - One-Click Startup Script
REM ===========================================================================
REM
REM Automated startup for competition/demo:
REM 1. Verifies all prerequisites
REM 2. Pre-warms Ollama model
REM 3. Starts backend
REM 4. Provides URLs (ngrok, local, etc.)
REM
REM ===========================================================================

setlocal enabledelayedexpansion

title PALLAVI Demo Startup

cd /d "%~dp0"

REM Colors for output (Windows doesn't support ANSI, so we use text)
echo.
echo ===========================================================================
echo  PALLAVI DEMO - STARTUP ORCHESTRATION
echo ===========================================================================
echo.

REM Step 1: Check Python
echo [1/6] Checking Python 3...
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 3 not found
    echo [ACTION] Install from https://www.python.org/
    exit /b 1
)
python --version
echo [OK] Python available
echo.

REM Step 2: Check Ollama
echo [2/6] Checking Ollama...
ollama version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Ollama not running
    echo [ACTION] Start Ollama: ollama serve (in new terminal)
    echo [ACTION] Or install: https://ollama.com/download
    exit /b 1
)
echo [OK] Ollama running
echo.

REM Step 3: Pre-warm model
echo [3/6] Pre-warming Ollama model...
call prewarm_ollama.bat
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Pre-warm failed, but continuing...
)
echo.

REM Step 4: Check .env
echo [4/6] Checking configuration...
if not exist ".env" (
    echo [ERROR] .env file not found
    echo [ACTION] Copy from .env.example: copy .env.example .env
    echo [ACTION] Update with your credentials (Exotel, Twilio, etc.)
    exit /b 1
)
echo [OK] .env file found
echo.

REM Step 5: Health check
echo [5/6] Checking backend health...
timeout /t 2 /nobreak > nul

curl -s http://127.0.0.1:8000/health > nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Backend already running on port 8000
) else (
    echo [INFO] Backend not yet running (this is OK, will start it)
)
echo.

REM Step 6: Information
echo [6/6] Startup information
echo.
echo ===========================================================================
echo  NEXT STEPS
echo ===========================================================================
echo.
echo [1] Start Backend (terminal 1):
echo     cd C:\Users\JAYAN\Downloads\NII
echo     uvicorn app.main:app --host 127.0.0.1 --port 8000
echo.
echo [2] Start ngrok tunnel (terminal 2):
echo     ngrok http 8000 --region=in
echo     (Copy public URL and update: PUBLIC_BASE_URL in .env)
echo.
echo [3] Run tests (this terminal):
echo     python qa_run.py
echo.
echo [4] View dashboard:
echo     http://localhost:5173
echo.
echo ===========================================================================
echo  DEMO CHECKLIST
echo ===========================================================================
echo.
echo [ ] Ollama pre-warmed (check: above says "OK")
echo [ ] Backend running on port 8000
echo [ ] ngrok tunnel active and PUBLIC_BASE_URL updated
echo [ ] All tests passing (qa_run.py)
echo [ ] Twilio SMS sent successfully
echo [ ] One full call-to-ticket created and visible in dashboard
echo.
echo ===========================================================================
echo  EMERGENCY CHECKS
echo ===========================================================================
echo.
echo Backend Health:
curl -s http://127.0.0.1:8000/health | findstr /C:"status"
echo.
echo Ollama Model:
ollama list | findstr /C:"phi3"
echo.
echo .env Status:
if exist ".env" (
    echo   [OK] .env file exists
) else (
    echo   [ERROR] .env file missing
)
echo.
echo ===========================================================================
echo  READY FOR DEMO
echo ===========================================================================
echo.
echo When all checks above are green, you're ready to demo!
echo.
echo Key endpoints:
echo   Health:             http://localhost:8000/health
echo   Process Text:       POST http://localhost:8000/process-text
echo   Analytics:          http://localhost:8000/analytics/summary
echo   Dashboard:          http://localhost:5173
echo.
echo For detailed guide, see: DEMO_GUIDE.md
echo.
pause
