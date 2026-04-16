# VaaniSeva

VaaniSeva is an AI-powered grievance management platform with:
- FastAPI backend for voice intake, ticket lifecycle, analytics, RBAC, escalation, cost telemetry, and privacy workflows.
- React + Vite analytics dashboard for admin and department users.

## Features

- JWT authentication (`/auth/login`, `/auth/logout`, `/auth/me`, `/auth/validate`)
- Role-based access control (admin and department scope)
- Department management APIs (CRUD + SLA policy)
- Ticket workflow: `created -> assigned -> in_progress -> resolved -> closed`
- SLA breach tracking and escalation chain rules
- Cost telemetry (`call_telemetry`) with summary endpoints
- Multilingual response generation endpoint
- Data deletion/privacy request tracking

## Project Structure

- `app/` - FastAPI backend (routes, services, models, utils)
- `analytics-ui/` - React frontend
- `data/` - local SQLite database files
- `requirements.txt` - backend dependencies

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

## Backend Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` (or copy from `.env.example`) with minimum required values:

```env
SQLITE_DB_PATH=data/vaaniseva.db
JWT_SECRET=change-this-in-production
JWT_EXPIRY_HOURS=24
CITY_ID=coimbatore
ORGANIZATION_NAME=VaaniSeva
```

Run backend:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

- `GET http://localhost:8000/health`

## Frontend Setup

```powershell
cd analytics-ui
npm install
npm run dev
```

Frontend runs on Vite default URL (typically `http://localhost:5173`).

Optional frontend environment:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Default Demo Users

- `admin` / `admin123`
- `pwd_officer` / `pwd123`
- `water_officer` / `water123`
- `sanitation` / `sanit123`

## Key API Groups

- Authentication: `/auth/*`
- Departments: `/departments/*`
- Tickets and analytics: `/tickets/*`, `/analytics/*`
- Escalation: `/escalation/*`
- i18n response: `/i18n/response`
- Privacy deletion: `/data-deletion-request/{mobile}`, `/analytics/deletion-status/{deletion_id}`

## Notes

- SQLite is used for local development.
- Token revocation blacklist is currently in-memory.
- Keep secrets out of source control.

## Production Recommendations

- Use persistent token blacklist (Redis).
- Move demo users to DB-managed users and rotate credentials.
- Put API behind HTTPS reverse proxy.
- Add CI checks for lint/test/build.
