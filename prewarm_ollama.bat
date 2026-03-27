@echo off
REM ===========================================================================
REM PALLAVI Ollama Pre-warm Script
REM ===========================================================================
REM
REM CRITICAL: Run this BEFORE demo/testing to keep model in memory
REM Expected: Loads model, saves ~1-2 seconds on first request
REM
REM ===========================================================================

echo.
echo ===========================================================================
echo OLLAMA PRE-WARM SCRIPT
echo ===========================================================================
echo.
echo [INFO] This script loads the Ollama model into memory for faster inference
echo [INFO] Expected time: 10-30 seconds (one-time operation)
echo.

REM Check if Ollama is running
ollama version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Ollama not found or not running
    echo [ACTION] Install Ollama: https://ollama.com/download
    echo [ACTION] Or run: ollama serve (in separate terminal)
    exit /b 1
)

echo [OK] Ollama CLI is available
echo.

REM Get configured model from environment (default: phi3:mini)
if "%OLLAMA_MODEL%"=="" (
    set "MODEL=phi3:mini"
) else (
    set "MODEL=%OLLAMA_MODEL%"
)

echo [STEP 1] Checking if model is installed...
ollama list | findstr /C:"%MODEL%"
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Model '%MODEL%' not found locally
    echo [ACTION] Pull model: ollama pull %MODEL%
    echo           This may take 5-10 minutes on first run
    exit /b 1
)

echo [OK] Model '%MODEL%' is installed
echo.

echo [STEP 2] Pre-warming model (loading into memory)...
echo [INFO] Sending dummy request to load model...
echo.

REM Pre-warm with a simple request
(
    echo {
    echo   "model": "%MODEL%",
    echo   "prompt": "What is 2+2? Answer: ",
    echo   "stream": false,
    echo   "options": {
    echo     "num_predict": 5,
    echo     "temperature": 0.1
    echo   }
    echo }
) | curl -X POST http://localhost:11434/api/generate -H "Content-Type: application/json" -d @- > nul 2>&1

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to connect to Ollama at localhost:11434
    echo [ACTION] Ensure Ollama is running: ollama serve
    exit /b 1
)

echo [OK] Model pre-warmed successfully
echo.

echo ===========================================================================
echo RESULT: Model is now in memory and ready for fast inference
echo ===========================================================================
echo.
echo [INFO] Model will stay warm for ~5-10 minutes of inactivity
echo [TIP]  Before demo, run this script again to ensure optimal performance
echo [TIP]  Keep terminal open or add to startup if running long sessions
echo.

exit /b 0
