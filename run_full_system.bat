@echo off
setlocal

REM ==========================================
REM PALLAVI Full System Launcher (Windows)
REM Starts: Ollama, Backend, Frontend, ngrok
REM ==========================================

echo.
echo [INFO] Starting PALLAVI full system...
echo [INFO] Script directory: %~dp0
echo.

REM Move to project root (where this .bat is located)
cd /d "%~dp0"

REM -----------------------------
REM 1) Start Ollama (phi3:mini)
REM -----------------------------
echo [STEP 1/6] Starting Ollama model (phi3:mini)...
start "PALLAVI - Ollama phi3" cmd /k "echo [OLLAMA] Launching phi3:mini... && ollama run phi3:mini"

echo [OK] Ollama start command issued.
echo.

REM -----------------------------
REM 2) Start Backend (FastAPI)
REM -----------------------------
echo [STEP 2/6] Starting backend on port 8000...
start "PALLAVI - Backend" cmd /k cd /d "%~dp0app" ^&^& echo [BACKEND] Starting uvicorn... ^&^& uvicorn main:app --reload --port 8000

echo [OK] Backend start command issued.
echo.

REM -----------------------------
REM 3) Start Frontend (Vite)
REM -----------------------------
echo [STEP 3/6] Starting frontend (Vite) on port 5173...
start "PALLAVI - Frontend" cmd /k cd /d "%~dp0analytics-ui" ^&^& echo [FRONTEND] Running npm dev server... ^&^& npm run dev

echo [OK] Frontend start command issued.
echo.

REM -----------------------------
REM 4) Start ngrok tunnel
REM -----------------------------
echo [STEP 4/6] Starting ngrok tunnel for backend (8000)...
start "PALLAVI - ngrok" cmd /k "echo [NGROK] Opening tunnel to http://localhost:8000 ... && ngrok http 8000"

echo [OK] ngrok start command issued.
echo.

REM -----------------------------
REM 5) Wait for services
REM -----------------------------
echo [STEP 5/6] Waiting for services to initialize...
timeout /t 8 /nobreak >nul

echo [OK] Wait complete.
echo.

REM -----------------------------
REM 6) Open browser
REM -----------------------------
echo [STEP 6/6] Opening UI in browser: http://localhost:5173
start "" "http://localhost:5173"

echo.
echo [DONE] PALLAVI startup sequence triggered.
echo [NOTE] Check the opened terminal windows for service logs and errors.
echo.

endlocal
