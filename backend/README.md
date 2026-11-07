# Student Analytics

FastAPI + PostgreSQL + Redis + JWT auth, built on the OULAD student-performance dataset (see `data/README.md`).

## Run
```bash
cp .env.example .env        # then fill in secrets (SECRET_KEY, POSTGRES_PASSWORD, ...)
docker compose up --build   # migrations run automatically on start
curl localhost:8000/health
```
Docs: http://localhost:8000/docs

## Endpoints
| Method | Path | Access |
|---|---|---|
| GET | /health | public (checks DB + Redis) |
| POST | /auth/register | public (creates `student`) |
| POST | /auth/login | public (rate-limited via Redis, 5 failures / 15 min) |
| POST | /auth/logout | token (revokes it via Redis denylist) |
| GET | /auth/me | any authenticated user |
| GET | /auth/users | admin only |

A default admin (`admin@edustat.com` / `admin123`, overridable via ADMIN_EMAIL / ADMIN_PASSWORD in `.env`) is created on startup. Change the password in production.

## Tests
```bash
docker compose exec api pytest -v
```

## Stack
Python 3.12, FastAPI, SQLAlchemy 2 (async) + asyncpg, Alembic, PostgreSQL 16, Redis 7, PyJWT, argon2.
