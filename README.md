# VaaniSeva

VaaniSeva is a voice-first operations platform for civic and enterprise use cases. It converts incoming complaints or service requests into actionable tickets, routes them to the right department, tracks SLA performance, and provides role-based analytics through a modern dashboard.

## What This Repository Contains

- FastAPI backend for authentication, ticket lifecycle, routing, analytics, escalation, cost telemetry, privacy workflows, and voice/AI integration.
- React + Vite frontend dashboard for admin and department operations users.
- SQLite-based local persistence with startup migrations.
- Windows helper scripts for one-click local startup and call triggering.

## Core Capabilities

- JWT authentication (`/auth/login`, `/auth/logout`, `/auth/me`, `/auth/validate`)
- Role-based access control:
	- Admin: global visibility and management
	- Department: scoped access to own department data
- Department administration APIs (CRUD + SLA policy)
- Ticket workflow transitions:
	- `created -> assigned -> in_progress -> resolved -> closed`
- SLA breach monitoring and escalation chain handling
- Cost telemetry and cost summary endpoints
- Localized response generation (`/i18n/response`)
- Data deletion request tracking for privacy compliance

## Architecture Overview

### Backend

- Entry point: `app/main.py`
- Framework: FastAPI
- Storage: SQLite (`SQLITE_DB_PATH`, default `data/vaaniseva.db`)
- Startup behavior:
	- Runs DB initialization/migrations
	- Starts SLA monitoring service (configurable)
- Exposed health endpoint: `GET /health`

### Frontend

- Location: `analytics-ui/`
- Stack: React 18 + Vite + Tailwind + Recharts + React Router
- Dev proxy:
	- Frontend calls `/api/*`
	- Vite rewrites and forwards to backend `http://127.0.0.1:8000`
	- This enables easier remote access via tunnels without hardcoded backend origins

## Repository Layout

```text
app/                 FastAPI backend (routes, services, models, utils)
analytics-ui/        React dashboard
data/                SQLite database files
requirements.txt     Python dependencies
START_ALL_SYSTEMS.bat  One-click local startup (backend + frontend)
START_BACKEND.bat      Backend-only startup
RUN_EVERYTHING.bat     Wrapper around full startup
TRIGGER_CALL.bat       Outbound call trigger utility
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+
- PowerShell (Windows workflows/scripts)

## Quick Start

### 1) Clone and create Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) Configure environment

Copy `.env.example` to `.env` and set at least the required values.

Required minimum for local auth + dashboard:

```env
SQLITE_DB_PATH=data/vaaniseva.db
JWT_SECRET=replace-with-a-strong-secret
JWT_EXPIRY_HOURS=24
CITY_ID=coimbatore
ORGANIZATION_NAME=VaaniSeva
SLA_MONITOR_ENABLED=false
```

AI provider (local default):

```env
AI_MODEL_PROVIDER=local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini
```

Optional integrations (set only if used):

- Twilio voice/messaging credentials
- Exotel inbound/outbound credentials
- Whisper/Groq STT credentials
- Bhashini credentials
- Lyzr API key

### 3) Run backend

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Health check:

- `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

### 4) Run frontend

```powershell
cd analytics-ui
npm install
npm run dev
```

Frontend:

- `http://127.0.0.1:5173`

## One-Click Startup Scripts (Windows)

- `START_ALL_SYSTEMS.bat`
	- Verifies Python/Node
	- Clears ports `8000` and `5173`
	- Optionally starts Ollama if installed
	- Starts backend and frontend in separate terminals
- `START_BACKEND.bat`
	- Backend-only startup with runtime config echo
- `RUN_EVERYTHING.bat`
	- Convenience wrapper for `START_ALL_SYSTEMS.bat`

## Demo Credentials

These are seeded in `app/routes/auth_routes.py` for local testing:

- `admin` / `admin123` (admin)
- `pwd_officer` / `pwd123` (department: PWD)
- `water_officer` / `water123` (department: Municipality)
- `sanitation` / `sanit123` (department: Sanitation)

## API Surface (High-Level)

### Authentication

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/validate`

### Department Management

- `GET /departments`
- `POST /departments` (admin)
- `GET /departments/{department_id}`
- `PUT /departments/{department_id}` (admin)
- `DELETE /departments/{department_id}` (admin)
- `GET /departments/{department_id}/sla-policy`

### Tickets and Workflow

- `GET /tickets`
- `GET /tickets/{ticket_id}`
- `PATCH /tickets/{ticket_id}/status`
- `POST /resolve-ticket/{ticket_id}`
- `POST /tickets/{ticket_id}/transition/in-progress`
- `POST /tickets/{ticket_id}/transition/closed`

### Analytics

- `GET /analytics/summary`
- `GET /analytics/metrics`
- `GET /analytics/issues`
- `GET /analytics/regions`
- `GET /analytics/sla`
- `GET /analytics/audit-summary`
- `GET /analytics/audit-timeline`
- `POST /sla-monitor`

### Cost and Escalation

- `POST /analytics/log-cost`
- `GET /analytics/cost-summary` (admin)
- `GET /tickets/{ticket_id}/cost`
- `POST /escalation/rules` (admin)
- `GET /escalation/rules/{dept_id}`
- `POST /escalation/trigger/{ticket_id}`
- `GET /tickets/{ticket_id}/escalation-history`

### Privacy and Localization

- `DELETE /tickets/{ticket_id}` (admin, soft delete)
- `POST /data-deletion-request/{mobile}` (admin)
- `GET /analytics/deletion-status/{deletion_id}` (admin)
- `GET /i18n/response`

## Voice and Call Testing

Use `TRIGGER_CALL.bat` to hit outbound calling endpoint:

```powershell
TRIGGER_CALL.bat +919999999999 "Please describe your complaint after the beep"
```

This posts to:

- `POST http://127.0.0.1:8000/outbound-call`

## Development Notes

- CORS currently allows:
	- `http://localhost:5173`
	- `http://127.0.0.1:5173`
- Frontend should call backend through `/api` in dev mode.
- DB migrations are executed via startup initialization.
- Token revocation blacklist is in-memory (non-persistent).

## Troubleshooting

### Frontend login fails when opened through remote tunnel

- Ensure frontend is using `/api` calls (not hardcoded localhost API URL).
- Ensure Vite dev server proxy is enabled in `analytics-ui/vite.config.js`.
- Confirm backend is up at `http://127.0.0.1:8000/health`.

### Port already in use

- Use `START_ALL_SYSTEMS.bat` which auto-cleans ports `8000` and `5173`.
- Or manually kill conflicting process and restart.

### Missing dependencies

- Backend: `pip install -r requirements.txt`
- Frontend: `cd analytics-ui ; npm install`

## Production Hardening Checklist

- Replace demo users with DB-backed user management and rotation policy.
- Move token blacklist to Redis or another persistent store.
- Enforce HTTPS behind reverse proxy/load balancer.
- Add CI for tests, linting, dependency and secret scanning.
- Externalize observability (structured logs, metrics, tracing).
- Store secrets in secure secret manager, not in repo files.

## License and Usage

This repository is currently organized for prototype/hackathon velocity. Validate legal, compliance, and operational requirements before any production deployment.
