# QUICK Full System Live Test (First Time, Fast)

Use this once and you can run full inbound + outbound testing in 15-20 minutes.

## 0. Run prerequisite checker (fastest start)

Run this first:

```powershell
cd C:\Users\JAYAN\Downloads\NII
.\quick_prerequisites_check.bat
```

What it does automatically:

1. Checks required tools (`python`, `node`, `npm`, `ngrok`, `ollama`).
2. Validates required Twilio/BASE_URL keys in `.env`.
3. Installs frontend dependencies if missing.
4. Tries to prewarm Ollama using `prewarm_ollama.bat`.

## 1. What must be ready

1. Ollama running locally.
2. Backend dependencies installed.
3. Twilio credentials present in `.env` (voice + SMS/WhatsApp).
4. Twilio phone number purchased and voice-enabled.
5. ngrok installed.

## 2. Start ngrok first (important)

Run:

```powershell
cd C:\Users\JAYAN\Downloads\NII
ngrok http 8000 --region=in
```

Copy the HTTPS URL from ngrok, example:

`https://abc123.ngrok-free.app`

Now update `.env`:

1. `BASE_URL=https://abc123.ngrok-free.app`
2. `PUBLIC_BASE_URL=https://abc123.ngrok-free.app`

Save `.env`.

## 3. Twilio website setup (inbound call)

Go to Twilio Console and open your purchased number voice settings.

Set incoming call webhook URL to:

`https://abc123.ngrok-free.app/incoming-call`

Use method: `POST`.

Notes:

1. You do NOT need to manually set recording callback URL in dashboard for this flow.
2. Backend returns XML with `<Record action=".../process-recording">` automatically.
3. So after inbound webhook is correct, recording callback is handled automatically.

## 4. Start backend

Run:

```powershell
cd C:\Users\JAYAN\Downloads\NII
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check in another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected: `status: ok`.

## 5. Quick local smoke checks

### 5.1 Inbound webhook endpoint

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/incoming-call" `
  -Method Post `
  -ContentType "application/x-www-form-urlencoded" `
  -Body @{ CallSid = "qa-in-001"; From = "+919876543210" } `
  -UseBasicParsing
```

Expected:

1. HTTP 200
2. XML response with welcome + record instruction

### 5.2 Outbound endpoint

```powershell
$body = @{ mobile = "+919876543210"; message = "Test outbound from PALLAVI" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/outbound-call" -Method Post -ContentType "application/json" -Body $body
```

Expected:

1. If Twilio voice credentials are valid: success response with provider payload
2. If credentials are wrong/missing: provider error (fix credentials/account access)

## 6. Real inbound test from phone (actual Twilio flow)

1. Dial your Twilio inbound number.
2. Speak complaint after beep.
3. You should hear: "Thank you. Please wait while we process your request."
4. System should continue processing in background.

If this works, inbound call setup is confirmed end-to-end.

## 7. Verify ticket + analytics after real call

Run:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/tickets
Invoke-RestMethod http://127.0.0.1:8000/analytics/summary
Invoke-RestMethod http://127.0.0.1:8000/analytics/metrics
```

Expected:

1. New ticket exists
2. Analytics endpoints return HTTP 200

## 8. Frontend check (optional but recommended)

Run:

```powershell
cd C:\Users\JAYAN\Downloads\NII\analytics-ui
npm install
npm run dev
```

Open:

`http://localhost:5173/admin`

Expected:

1. Dashboard loads
2. New complaint/ticket reflected
3. Metrics panel visible

## 9. One-command QA confidence run

```powershell
cd C:\Users\JAYAN\Downloads\NII
python qa_run.py
```

Expected: all tests pass and report generated.

## 10. Fast troubleshooting

1. ngrok URL changed after restart:
- Update `BASE_URL` and `PUBLIC_BASE_URL` again.
- Re-save Twilio inbound webhook URL to new ngrok URL.

2. Inbound returns 400:
- Confirm Twilio is calling `/incoming-call` with form data.

3. Outbound returns provider error:
- Verify outbound account SID/token/number in `.env`.
- Ensure backend restarted after `.env` change.

4. No SMS/WhatsApp:
- Check Twilio credentials and WhatsApp sender approval/sandbox status.

## 11. Done criteria

You are fully ready when all below are true:

1. Real phone call to inbound number reaches your backend and records complaint.
2. `/outbound-call` succeeds for a real mobile number.
3. Ticket is created and visible via `/tickets` and dashboard.
4. `python qa_run.py` passes.
