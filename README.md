# Performance Review & OKR Platform

React (Vite + TypeScript) + Django REST Framework + PostgreSQL. OKR goal
setting with check-in-driven progress rollups, a guarded review-cycle state
machine (self -> manager -> peer -> calibration), 360 peer feedback with
anonymity + a minimum-reviewer release threshold, and calibration.

## Run with Docker (requires Docker Desktop / Docker Engine)

```
cp .env.example .env
docker compose up --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

- Backend: http://localhost:8000/api/
- Frontend: http://localhost:5173/

## Run the backend without Docker (dev-only SQLite override)

```
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
set USE_SQLITE=True
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Run tests (same SQLite + eager-Celery override, via `config.settings.test`):

```
python manage.py test --settings=config.settings.test
```

## Run the frontend

```
cd frontend
npm install
npm run dev
```

## Architecture

```
React SPA --HTTPS/JWT--> Django REST API --ORM--> PostgreSQL
                              |--enqueue--> Redis --> Celery worker/beat --> Email
```

Celery is used only where genuinely justified: feedback-request emails
(sent immediately on request creation) and a nightly deadline-reminder
sweep (config/celery.py beat schedule). Review-cycle STAGE transitions are
never auto-applied by beat - they always require an explicit, guarded
`POST /api/cycles/{id}/transition/` call, since the guard conditions
(manager reviews submitted, calibration resolved) require a human
decision.

See `backend/apps/okrs/services.py` (progress rollup),
`backend/apps/reviews/state_machine.py` (cycle state machine) and
`backend/apps/feedback/permissions.py` (peer-feedback anonymity) for the
core business logic.
