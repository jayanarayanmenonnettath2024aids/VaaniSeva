# Full System UI Test Guide (Simple)

This guide helps you test the full system quickly through the UI.

## 1) Before You Start

Make sure these are ready:
- `.env` has valid Twilio Voice and Twilio Messaging credentials
- `BASE_URL` in `.env` is your current ngrok HTTPS URL
- Twilio voice webhook is set to: `https://<your-ngrok-url>/incoming-call` (POST)

## 2) Start Everything

Open Command Prompt in project root and run:

```bat
START_ALL_SYSTEMS.bat
```

Note: this launcher forces `SLA_MONITOR_ENABLED=false` for that run to prevent SMS 429 flood during demo/testing.

This should open:
- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

If ngrok is not running, start it in another terminal:

```bash
ngrok http 8000
```

Then update `.env` `BASE_URL` if ngrok URL changed.

## 3) Quick Health Check

Open in browser:
- `http://127.0.0.1:8000/health`

Expected:

```json
{"status":"ok","modules":["voice","ai","action"]}
```

## 4) Test Through UI (Main Flow)

Open UI:
- `http://127.0.0.1:5173/admin`

Now check these pages one by one:

### A) Admin Pages
- `http://127.0.0.1:5173/admin`
- `http://127.0.0.1:5173/admin/geography`
- `http://127.0.0.1:5173/admin/issues`
- `http://127.0.0.1:5173/admin/sla`
- `http://127.0.0.1:5173/admin/performance`

Pass if:
- Page loads without blank screen
- Charts/cards/tables render
- No red errors in browser console

### B) Department Pages
- `http://127.0.0.1:5173/department`
- `http://127.0.0.1:5173/department/heatmap`
- `http://127.0.0.1:5173/department/tickets`
- `http://127.0.0.1:5173/department/performance`

Pass if:
- Data appears and navigation works
- Ticket list loads

### C) Public Pages
- `http://127.0.0.1:5173/public`
- `http://127.0.0.1:5173/public/explorer`
- `http://127.0.0.1:5173/public/trends`

Pass if:
- Public charts/heatmaps load
- Filters/interactions respond

## 5) End-to-End Functional Test (Real or No-International)

### Option A: Real call flow (if international calling is allowed)

Do one real call flow:
1. Call your Twilio voice number from a phone
2. Speak a complaint clearly
3. Wait for processing
4. Open `http://127.0.0.1:5173/admin` and `http://127.0.0.1:5173/department/tickets`

Pass if:
- New ticket appears
- Issue category/department/SLA fields are populated
- Dashboard counts update

### Option B: No-international testing (recommended for India dev testing)

If you cannot call a US Twilio number from India, trigger inbound simulation from local API:

```bash
python -c "import requests; r=requests.post('http://127.0.0.1:8000/incoming-call', data={'CallSid':'SIM-IN-001','From':'+917867896369'}); print(r.status_code); print(r.text[:200])"
python -c "import requests; r=requests.post('http://127.0.0.1:8000/simulate-recording', json={'text':'There is a pothole and streetlight issue near MG Road'}); print(r.status_code, r.json())"
```

Pass if:
- `incoming-call` returns `200` with TwiML XML
- `simulate-recording` returns `status: ok`
- New ticket appears in Admin/Department UI

## 6) Outbound Call Test

### Option A: Real outbound call

Use backend endpoint:

```bash
python -c "import requests; r=requests.post('http://127.0.0.1:8000/outbound-call', json={'mobile':'+917867896369','message':'Test outbound call'}); print(r.status_code, r.text)"
```

Pass if:
- Status is `200`
- You receive the call on target mobile

### Option B: Outbound trigger validation (no international call)

You can still verify that your backend triggers Twilio correctly without placing a real call:

```bash
python -c "import requests; r=requests.post('http://127.0.0.1:8000/outbound-call', json={'mobile':'+917867896369','message':'Test outbound trigger'}); print(r.status_code); print(r.text)"
```

Interpretation:
- `200`: Twilio accepted call request
- `502` with Twilio error: trigger worked, provider blocked/rejected destination
- `500`: app-side issue

To make real outbound from Twilio trial to India, you must enable India geo permissions and verify destination number in Twilio.

## 7) Messaging Test (SMS/WhatsApp)

Create a test event from your app flow that triggers notification (for example ticket action/escalation), then verify:
- SMS/WhatsApp received
- No Twilio errors in backend log

## 8) If Something Fails

### A) UI not loading data
- Confirm backend health endpoint is OK
- Hard refresh browser (`Ctrl+F5`)

### B) Twilio call fails
- Check Twilio Voice webhook URL is correct and POST
- Ensure ngrok URL is alive and same as `.env` `BASE_URL`

### C) SMS fails with network/DNS error
- Run:

```powershell
nslookup api.twilio.com
ping api.twilio.com
```

If DNS fails, fix network/DNS first.

## 9) Final Pass Checklist

Mark all done:
- [ ] Backend health OK
- [ ] Admin pages load
- [ ] Department pages load
- [ ] Public pages load
- [ ] Real inbound call creates ticket
- [ ] Outbound call works
- [ ] SMS/WhatsApp notification works
- [ ] No major errors in backend logs

If all are checked, your full system is ready for demo.

