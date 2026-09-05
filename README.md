# Attendance Management App

Open-source, Python-first attendance management MVP based on the approved
frontend, middleware, backend, and data architecture.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/> for the starter web client and
<http://127.0.0.1:8000/docs> for the API.

The default database is SQLite for a zero-configuration pilot. Set
`DATABASE_URL` to PostgreSQL for deployment.

## Run with PostgreSQL

```bash
docker compose up --build
```

The API is available at <http://127.0.0.1:8000>.

## Mobile deployment

The Flutter app connects to a deployed FastAPI URL; mobile operating systems
cannot start this Python service as part of `flutter run`. Supply the backend
URL at launch or build time:

```bash
cd mobile
flutter run --dart-define=API_BASE_URL=https://attendance-api.example.com
```

## Current MVP capabilities

- Role-aware users and administrative jurisdiction (`state`, `district`, `block`, `school`)
- School and student master data
- Attendance creation and filtered listing
- Idempotent offline batch synchronization
- Correction status field ready for approval workflow
- Responsive administrator dashboard served from the same origin
- Dashboard summary, school directory, and student attendance views
- API-key protected read and write endpoints with interactive OpenAPI docs
- PostgreSQL/PostGIS-ready persistence configuration

## Backend structure

The backend is organized by business domain so each module can evolve into a
separate service without changing the public API:

```text
backend/
├── app/
│   ├── main.py
│   ├── config/ auth/ users/ organizations/
│   ├── schools/ students/ staff/ attendance/
│   ├── biometric/ devices/ leave/ payroll/
│   ├── reports/ notifications/ audit/ sync/
│   └── db.py models.py schemas.py
├── workers/
├── migrations/
├── tests/
└── pyproject.toml
```
