@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
set "FAILED=0"

echo ==============================================
echo  PALLAVI Quick Prerequisites Check
echo ==============================================
echo.

if not exist ".env" (
  echo [ERROR] .env file not found in project root.
  set "FAILED=1"
  goto :summary
)

call :checkTool python
call :checkTool node
call :checkTool npm
call :checkTool ngrok
call :checkTool ollama
echo.

call :checkEnv EXOTEL_SID_INBOUND
call :checkEnv EXOTEL_TOKEN_INBOUND
call :checkEnv EXOTEL_NUMBER_INBOUND
call :checkEnv EXOTEL_SID_OUTBOUND
call :checkEnv EXOTEL_TOKEN_OUTBOUND
call :checkEnv EXOTEL_NUMBER_OUTBOUND
call :checkEnv TWILIO_ACCOUNT_SID
call :checkEnv TWILIO_AUTH_TOKEN
call :checkEnv TWILIO_PHONE_NUMBER
call :checkEnv TWILIO_WHATSAPP_NUMBER
call :checkEnv BASE_URL
echo.

if not exist "analytics-ui\node_modules" (
  echo [INFO] Frontend dependencies not found. Running npm install...
  pushd analytics-ui
  call npm install
  if errorlevel 1 (
    echo [ERROR] npm install failed in analytics-ui.
    set "FAILED=1"
  ) else (
    echo [OK] Frontend dependencies installed.
  )
  popd
) else (
  echo [OK] Frontend dependencies already present.
)

echo.
echo [INFO] Checking Ollama service and model readiness...
ollama list >nul 2>&1
if errorlevel 1 (
  echo [WARN] Ollama service not reachable right now. Start it with: ollama serve
) else (
  echo [OK] Ollama service is reachable.
  if exist "prewarm_ollama.bat" (
    echo [INFO] Running prewarm_ollama.bat...
    call prewarm_ollama.bat
    if errorlevel 1 (
      echo [WARN] Prewarm script reported issues. Continue after fixing Ollama/model.
    ) else (
      echo [OK] Ollama prewarm completed.
    )
  ) else (
    echo [WARN] prewarm_ollama.bat not found. Skipping prewarm.
  )
)

:summary
echo.
echo ==============================================
if "%FAILED%"=="0" (
  echo [DONE] Prerequisite check completed.
  echo Next:
  echo   1) Start backend: uvicorn app.main:app --host 127.0.0.1 --port 8000
  echo   2) Start ngrok:   ngrok http 8000 --region=in
  echo   3) Update Exotel inbound webhook to: https://YOUR-NGROK-URL/incoming-call
  exit /b 0
) else (
  echo [DONE WITH ERRORS] Fix the errors above, then run this file again.
  exit /b 1
)

:checkTool
where %~1 >nul 2>&1
if errorlevel 1 (
  echo [ERROR] %~1 not found in PATH.
  set "FAILED=1"
) else (
  echo [OK] %~1 found.
)
goto :eof

:checkEnv
set "_k=%~1"
set "_v="
for /f "tokens=1,* delims==" %%A in ('findstr /b /c:"%_k%=" ".env"') do (
  set "_v=%%B"
)
if not defined _v (
  echo [ERROR] %_k% missing in .env
  set "FAILED=1"
  goto :eof
)
if "%_v%"=="" (
  echo [ERROR] %_k% is empty in .env
  set "FAILED=1"
  goto :eof
)
echo [OK] %_k% is set.
goto :eof
