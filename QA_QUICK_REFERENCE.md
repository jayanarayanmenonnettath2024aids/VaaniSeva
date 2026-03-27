# PALLAVI QA Testing - Quick Reference Card

## One-Command QA Execution

```bash
# Recommended (Python, cross-platform)
python qa_run.py

# Alternative (PowerShell, Windows-native)
powershell -ExecutionPolicy Bypass -File qa_run.ps1

# With auto-backend check (batch wrapper)
qa_run_all.bat
```

---

## Pre-Test Checklist

- [ ] Backend running: `uvicorn app.main:app --port 8000`
- [ ] Database exists: `data/pallavi.db`
- [ ] Ollama loaded: `ollama ps` shows model running
- [ ] Python/PowerShell available: `python --version` OR `pwsh -Version`

---

## Quick Test Reference

### Minimum Smoke Tests (30 sec)

```bash
# Just health check
curl http://127.0.0.1:8000/health

# All smoke endpoints (via script)
python qa_run.py
```

### Full E2E Validation (60 sec)

```bash
# Runs: health + workflows + integration + negative + DB checks
python qa_run.py > qa_results.txt 2>&1 && cat qa_results.txt
```

### Database Validation Only

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('data/pallavi.db')
print('Migrations:', conn.execute('SELECT COUNT(*) FROM schema_migrations').fetchone()[0])
print('Tickets:', conn.execute('SELECT COUNT(*) FROM tickets').fetchone()[0])
print('Audit Events:', conn.execute('SELECT COUNT(*) FROM audit_timeline').fetchone()[0])
conn.close()
"
```

---

## Test Results Interpretation

| Result | Meaning | Action |
|--------|---------|--------|
| ✓ ALL TESTS PASSED | System healthy | Deploy / Monitor |
| ✗ SOME TESTS FAILED | Issues present | Review report + fix |
| ✗ Backend not responding | Service down | Start backend |
| ✗ Database not found | DB missing | Initialize DB |

---

## Common Test Scenarios

### Scenario A: Verify Core API Working

```bash
# Single command that tests all endpoints
python qa_run.py 2>&1 | grep -E "PASS|FAIL|Summary"
```

### Scenario B: Test Full Workflow (Voice → Action)

```bash
# Integration test will run this automatically
# Manual check:
curl -X POST http://127.0.0.1:8000/incoming-call \
  -d "CallSid=test-1&From=%2B919999999999"

curl -X POST http://127.0.0.1:8000/process-text \
  -H "Content-Type: application/json" \
  -d '{"call_id":"test-1","mobile":"+919999999999","text":"pothole"}'

curl http://127.0.0.1:8000/tickets
```

### Scenario C: Check Data Privacy (No Raw PII in Audit)

```bash
python3 -c "
import sqlite3, json
conn = sqlite3.connect('data/pallavi.db')
row = conn.execute('SELECT call_ref, mobile_ref, meta_json FROM audit_timeline LIMIT 1').fetchone()
if row:
    print('call_ref (hashed):', row[0][:20] + '...' if row[0] else None)
    print('mobile_ref (hashed):', row[1][:20] + '...' if row[1] else None)
    meta = json.loads(row[2])
    print('Metadata fields:', list(meta.keys()))
conn.close()
"
```

### Scenario D: Performance Baseline

```bash
# Health endpoint latency (should be ~20ms)
powershell -Command "
  1..10 | ForEach-Object {
    \$t = Measure-Command { 
      iwr http://127.0.0.1:8000/health -UseBasicParsing > \$null 
    }
    Write-Host \$t.TotalMilliseconds
  } | Measure-Object -Average
"
```

---

## Report Files Generated

| File | Format | Purpose |
|------|--------|---------|
| `qa_report.txt` | Plain text | Human-readable results (PowerShell) |
| `qa_report_python.json` | JSON | Machine-readable results (Python) |

View reports:
```bash
# PowerShell report
type qa_report.txt

# Python JSON report
type qa_report_python.json
# or pretty-print:
python -m json.tool qa_report_python.json
```

---

## Troubleshooting Quick Fixes

| Error | Solution |
|-------|----------|
| `Connection refused` | `uvicorn app.main:app --port 8000` |
| `ModuleNotFoundError: requests` | `pip install requests` |
| `ExecutionPolicy` | `powershell -ExecutionPolicy Bypass -File qa_run.ps1` |
| `database locked` | Kill old Python process: `taskkill /F /IM python.exe` |
| `Ollama not found` | Load model: `ollama run neural-chat` |

---

## Schedule QA Tests Hourly (Windows Task Scheduler)

```powershell
# Run as Administrator
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "qa_run.py" `
  -WorkingDirectory "C:\Users\JAYAN\Downloads\NII"
$trigger = New-ScheduledTaskTrigger -At 9:00AM -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 365)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
Register-ScheduledTask -TaskName "PALLAVI-QA-Hourly" -Action $action -Trigger $trigger -Principal $principal -Force
```

---

## Pass/Fail Thresholds

### PASS Criteria ✓
- All smoke endpoints return 200
- Integration workflow completes end-to-end
- No 500 errors or crashes
- DB has ≥4 migrations applied
- Audit records are hashed (no raw PII)

### FAIL Criteria ✗
- Any endpoint returns 5xx error
- Backend crashes during test
- Integration flow breaks at any stage
- DB migrations not applied
- Raw phone numbers found in audit logs

---

## Additional Resources

- **Full Testing Guide:** [QA_TESTING_GUIDE.md](./QA_TESTING_GUIDE.md)
- **API Documentation:** [API_DOCS.md](./API_DOCS.md)
- **Backend Logs:** `app.log` (if configured)
- **Database Explorer:** `sqlite3 data/pallavi.db` (command-line SQL)

---

**TL;DR — Just run this:**

```bash
python qa_run.py
```

**Expected output after ~60 seconds:**
```
✓ ALL TESTS PASSED
Tests Passed: 32
Tests Failed: 0
```

---

*Generated: March 27, 2026*
*PALLAVI Multi-Module QA Suite v1.0*
