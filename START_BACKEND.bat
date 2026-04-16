@echo off
REM ============================================================================
REM PALLAVI: START BACKEND ONLY
REM ============================================================================
REM Starts FastAPI backend server on http://127.0.0.1:8000
REM Requires: Python 3.9+, ngrok tunnel active, .env configured
REM ============================================================================

echo.
echo ============================================================================
echo PALLAVI: BACKEND SERVER
echo ============================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9 or higher.
    exit /b 1
)

REM Kill any existing process on port 8000
echo [1/3] Cleaning up port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM Display configuration
echo [2/3] Loading configuration from .env...
echo.
echo Configuration:
python -c "from app.config import settings; print(f'  - BASE_URL: {settings.BASE_URL}'); print(f'  - AI Provider: {settings.AI_MODEL_PROVIDER}'); print(f'  - Admin Port: {settings.ADMIN_PORT}'); print(f'  - SLA Monitor: {settings.SLA_MONITOR_ENABLED}')" 2>nul
echo.

REM Start backend
echo [3/3] Starting backend server...
echo.
set SLA_MONITOR_ENABLED=false
echo SLA monitor forced OFF for this run (to avoid SMS rate-limit spam).
echo.
echo Backend is running at: http://127.0.0.1:8000
echo Health check: http://127.0.0.1:8000/health
echo.
echo Ensure ngrok tunnel is active for Twilio webhooks:
echo  - ngrok http 8000
echo  - Update BASE_URL in .env with ngrok URL
echo.
echo Press Ctrl+C to stop backend
echo ============================================================================
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
