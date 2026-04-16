@echo off
setlocal

set "API_URL=http://127.0.0.1:8000/outbound-call"

if "%~1"=="" (
  echo Usage: %~nx0 ^<mobile^> [message]
  echo Example: %~nx0 +919843398325 "Please describe your complaint after the beep"
  exit /b 1
)

set "MOBILE=%~1"
set "MESSAGE=%~2"

if "%MESSAGE%"=="" (
  set "MESSAGE=Please describe your complaint after the beep"
)

echo Triggering outbound call...
echo Mobile: %MOBILE%
echo Message: %MESSAGE%
echo Endpoint: %API_URL%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$body = @{ mobile = $env:MOBILE; message = $env:MESSAGE } | ConvertTo-Json -Compress; " ^
  "try { " ^
  "  $resp = Invoke-RestMethod -Uri $env:API_URL -Method Post -ContentType 'application/json' -Body $body; " ^
  "  Write-Host 'Success:'; " ^
  "  $resp | ConvertTo-Json -Depth 10; " ^
  "} catch { " ^
  "  Write-Host 'Request failed.'; " ^
  "  if ($_.Exception.Response) { " ^
  "    $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream()); " ^
  "    $txt = $sr.ReadToEnd(); " ^
  "    Write-Host $txt; " ^
  "  } else { " ^
  "    Write-Host $_.Exception.Message; " ^
  "  } " ^
  "  exit 1; " ^
  "}"

set "EXIT_CODE=%ERRORLEVEL%"
echo.
if "%EXIT_CODE%"=="0" (
  echo Done.
) else (
  echo Failed with exit code %EXIT_CODE%.
)

exit /b %EXIT_CODE%
