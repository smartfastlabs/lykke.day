# AGENTS.md

## Cursor Cloud specific instructions

### Architecture

Lykke.day is a wellbeing-first daily planner with a **Python FastAPI backend** (Clean Architecture + CQRS) and a **SolidJS frontend** (Vite + TailwindCSS PWA). All backend services run inside Docker containers.

### Services overview

| Service | How to start | Port |
|---|---|---|
| PostgreSQL 16 + Redis 7 | `make docker-up` (from `backend/`) | 5432 / 6379 |
| Backend API (FastAPI) | `make serve-http` (from `backend/`) | 8080 |
| API + Worker + Scheduler | `make serve` (from `backend/`) | 8080 |
| Frontend (Vite) | `npm run dev` (from `frontend/`) | 5173 |

### Starting the dev environment

1. Ensure Docker daemon is running (`sudo dockerd` if needed; socket at `/var/run/docker.sock` needs to be accessible, `sudo chmod 666 /var/run/docker.sock`).
2. `cd backend && make docker-up` — starts Postgres and Redis.
3. `make migrate-dev && make migrate-test` — runs Alembic migrations on both databases.
4. `make serve-http` — starts the API in Docker (foreground). Use `make serve` if you also need the worker and scheduler.
5. `cd ../frontend && npm run dev` — starts Vite dev server on port 5173.

### Backend `.env` file

The backend requires a `.env` file at `backend/.env`. Copy from `backend/.env.test` for local development:

```bash
cp backend/.env.test backend/.env
```

This provides test VAPID keys, session secret, and other required settings. Without it, the API will crash on startup (VAPID PEM parse error).

### Gotcha: test database init

The `docker/init-db.sh` script only runs on the **first** Postgres container start (when the volume is fresh). If the Postgres volume already exists but the `lykke_test` role is missing, manually create it:

```sql
CREATE DATABASE lykke_test;
CREATE USER lykke_test WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE lykke_test TO lykke_test;
-- Connect to lykke_test and run:
GRANT ALL ON SCHEMA public TO lykke_test;
```

### Running checks

See the README "Common Commands" section. Quick reference:

- **Backend tests**: `make test` (from `backend/`)
- **Backend typecheck**: `make typecheck` (from `backend/`)
- **Backend full check**: `make check` (runs typecheck + tests)
- **Frontend tests**: `npm run test` (from `frontend/`)
- **Frontend lint**: `npm run lint` (from `frontend/`)
- **Frontend typecheck**: `npm run type-check` (from `frontend/`)
- **Frontend full check**: `npm run check` (runs type-check + lint + test)

### Frontend requires Node.js 25.x

The frontend enforces Node 25 via a `check-node` pre-script. Use `nvm install 25 && nvm use 25` to switch.

### Frontend API proxy

The frontend makes relative `/api/*` fetch calls. In production these are proxied by Netlify. For local development, the Vite dev server on port 5173 does **not** proxy API calls. The app's WebSocket connections go directly to `localhost:8080`. A full local dev experience with API proxying requires Netlify CLI (`dev:local` script), but for most backend development, hitting the API directly at `localhost:8080` or using the Swagger UI at `localhost:8080/docs` is sufficient.
