# PALLAVI Full QA Testing Guide (Backend + Frontend + Voice + SMS + WhatsApp)

This guide is the single source of truth for running full system QA, from local API checks to provider-connected end-to-end testing.

## 1. Latest Run Status (Executed in this workspace)

Date: 2026-03-27

What was run:
1. Backend API QA: `python qa_run.py`
2. Frontend production build: `npm run build` in `analytics-ui`
3. Manual API spot checks for inbound voice, action flow, and outbound call

Observed result summary:
1. Python QA suite: 31/31 passed (report: `qa_report_python.json`)
2. Frontend build: success via Vite
3. `/process-action`: ticket created and notifications queued
4. `/outbound-call`: provider error expected when Twilio voice credentials are not configured

## 2. Test Modes

Use two modes to cover everything.

1. Mode A: Local QA (no provider credentials)
- Validates backend, AI/action integration, database persistence, audit logging, frontend build and dashboard behavior.

2. Mode B: Provider-connected E2E
- Validates real Twilio inbound/outbound calls and real Twilio SMS/WhatsApp delivery.
- Requires valid credentials and public webhook URL.

## 3. Prerequisites

## 3.1 System prerequisites

1. Python 3.8+
2. Node.js 18+
3. PowerShell (Windows)
4. SQLite DB file at `data/pallavi.db`

## 3.2 Required runtime services

1. Backend: FastAPI (`uvicorn app.main:app --host 127.0.0.1 --port 8000`)
2. Frontend: Vite (`npm run dev` in `analytics-ui`) for interactive checks

## 3.3 Provider prerequisites (for full external E2E)

Set these in `.env` for real provider testing:
1. Twilio:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `TWILIO_WHATSAPP_NUMBER`

2. Twilio Voice:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER` (or `TWILIO_VOICE_NUMBER`)

3. Public callback URL:
- `BASE_URL` must point to your public URL (for example ngrok)
- Example: `https://<id>.ngrok-free.app`

Without these values, provider tests will return skipped/error states, which is expected.

## 4. Full Test Execution Order

Run in this exact order for repeatable QA.

1. Backend startup and health
2. Automated API QA (`qa_run.py`)
3. Frontend build check
4. Frontend runtime check (optional but recommended)
5. Manual inbound/outbound voice checks
6. SMS and WhatsApp delivery checks
7. DB and audit validation
8. Final report capture

## 5. Step-by-Step Commands

All commands below are PowerShell-friendly.

## 5.1 Start backend

```powershell
cd C:\Users\JAYAN\Downloads\NII
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected: status `ok`

## 5.2 Run automated backend QA

```powershell
cd C:\Users\JAYAN\Downloads\NII
python qa_run.py
```

Expected:
1. `ALL TESTS PASSED`
2. JSON report saved to `qa_report_python.json`

Note:
- `qa_run.py` is the authoritative automated suite.
- If `qa_run.ps1` fails to parse, use `qa_run.py`.

## 5.3 Build frontend

```powershell
cd C:\Users\JAYAN\Downloads\NII\analytics-ui
npm install
npm run build
```

Expected:
1. Vite build succeeds
2. `dist/` generated

## 5.4 Run frontend for interactive QA

```powershell
cd C:\Users\JAYAN\Downloads\NII\analytics-ui
npm run dev
```

Open:
1. `http://localhost:5173/admin`
2. Confirm dashboard loads
3. Confirm KPI panels and charts render

## 6. Manual End-to-End Scenarios

## 6.1 Inbound voice webhook flow (Twilio-style)

This verifies `/incoming-call` accepts form webhook and returns TwiML XML.

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/incoming-call" \
  -Method Post \
  -ContentType "application/x-www-form-urlencoded" \
  -Body @{ CallSid = "qa-in-001"; From = "+919876543210" } \
  -UseBasicParsing
```

Expected:
1. HTTP 200
2. XML response containing welcome + record instruction

## 6.2 Recording callback flow

Validation case (deterministic):

```powershell
try {
  Invoke-WebRequest -Uri "http://127.0.0.1:8000/process-recording" \
    -Method Post \
    -ContentType "application/x-www-form-urlencoded" \
    -Body @{ CallSid = "qa-in-001"; RecordingUrl = "not-an-url" } \
    -UseBasicParsing
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

Expected:
1. HTTP 400 for invalid recording URL
2. No backend crash

Provider-connected case:
1. Twilio sends real recording URL
2. Endpoint returns processing feedback XML
3. AI forwarding continues asynchronously

## 6.3 AI to action flow (ticket creation)

```powershell
$body = @{
  call_id = "qa-action-001"
  structured_data = @{
    customer_name = "QA User"
    mobile = "+919876543210"
    issue = "Streetlight not working"
    location = "Anna Nagar"
    issue_type = "Electricity"
  }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://127.0.0.1:8000/process-action" \
  -Method Post -ContentType "application/json" -Body $body
```

Expected:
1. `ticket_id` created
2. `department` assigned
3. `notifications` is `queued`

## 6.4 Outbound call flow

```powershell
$body = @{ mobile = "+919876543210"; message = "Test outbound" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/outbound-call" \
  -Method Post -ContentType "application/json" -Body $body
```

Expected:
1. With valid Twilio voice config: HTTP 200 and provider response
2. Without Twilio voice config: provider error (expected)

## 6.5 SMS and WhatsApp E2E (Twilio)

Trigger via action flow (`/process-action`) because notifications are sent asynchronously there.

Local validation (without Twilio credentials):
1. Endpoint still returns success and `notifications: queued`
2. Twilio sender functions return `skipped` internally

Provider-connected validation:
1. Ensure all Twilio env vars are configured
2. Use a real test mobile in E.164 format (example `+9198xxxxxxxx`)
3. Call `/process-action`
4. Verify in Twilio Console:
- SMS message created and delivered/accepted
- WhatsApp message created and delivered/accepted
5. Verify mobile receives both messages

## 7. Frontend E2E Validation Checklist

After backend + frontend are running:

1. Open `http://localhost:5173/admin`
2. Verify dashboard widgets load without console errors
3. Trigger a new ticket using `/process-action`
4. Confirm live update badge appears on dashboard
5. Confirm metrics panel updates and displays values
6. Refresh page and confirm persisted ticket counts are reflected

## 8. Database and Audit Validation

Run these checks after E2E scenarios.

## 8.1 Ticket persistence

```powershell
Invoke-RestMethod http://127.0.0.1:8000/tickets
```

Expected: newly created ticket IDs present.

## 8.2 Analytics validation

```powershell
Invoke-RestMethod http://127.0.0.1:8000/analytics/summary
Invoke-RestMethod http://127.0.0.1:8000/analytics/issues
Invoke-RestMethod http://127.0.0.1:8000/analytics/regions
Invoke-RestMethod http://127.0.0.1:8000/analytics/sla
Invoke-RestMethod http://127.0.0.1:8000/analytics/audit-summary
Invoke-RestMethod http://127.0.0.1:8000/analytics/audit-timeline
Invoke-RestMethod http://127.0.0.1:8000/analytics/metrics
```

Expected:
1. HTTP 200 from all endpoints
2. Metrics endpoint returns resolution and workload stats

## 8.3 DPDP and audit safety checks

SQLite quick checks:

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/pallavi.db'); r=c.execute('select call_ref,mobile_ref,meta_json from audit_timeline order by id desc limit 5').fetchall(); print(r)"
```

Expected:
1. `call_ref` and `mobile_ref` are hashed references (no raw numbers)
2. metadata only includes allow-listed fields

## 9. Pass Criteria for Full Release QA

Mark QA complete only if all are true:

1. `qa_run.py` passes fully
2. Frontend build succeeds
3. Inbound voice webhook path returns valid XML
4. Action flow creates ticket and routes department
5. Outbound call succeeds (or provider-missing error is documented)
6. SMS and WhatsApp are verified in Twilio Console (provider-connected mode)
7. Analytics and metrics endpoints all return 200
8. Audit timeline entries created across voice, AI, action stages

## 10. Troubleshooting

1. Port busy on 8000
- Symptom: address already in use
- Fix: stop existing backend process, then restart uvicorn

2. Incoming call test returns 400
- Cause: JSON body used instead of form body
- Fix: use `application/x-www-form-urlencoded`

3. Outbound call returns 502
- Cause: Twilio voice credentials missing/invalid
- Fix: verify Twilio env values and `BASE_URL`

4. SMS/WhatsApp not received
- Cause: Twilio creds missing, sender not approved, sandbox limitations
- Fix: verify Twilio console settings and destination approval

5. Frontend build fails
- Fix sequence:
1. `cd analytics-ui`
2. `npm install`
3. `npm run build`

## 11. Minimal Daily Regression Command Set

Use this for quick confidence before demos:

```powershell
cd C:\Users\JAYAN\Downloads\NII
python qa_run.py
cd analytics-ui
npm run build
```

If both pass, baseline system health is good.
