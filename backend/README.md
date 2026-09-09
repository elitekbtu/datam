# Datam Backend

FastAPI + SQLAlchemy 2.0 (async) + Alembic on SQLite.

## Layout

```
backend/
├── main.py                 FastAPI app, CORS, router mounting
├── core/
│   ├── config.py           Settings (pydantic BaseSettings)
│   ├── settings.py         password hashing, JWT access/refresh, HTTPBearer
│   └── dependencies.py     DbSession, CurrentUser, OptionalUser, CurrentAdmin
├── database/
│   ├── base.py             DeclarativeBase + TimestampMixin
│   ├── session.py          async engine, session factory, get_db
│   ├── alembic.ini
│   └── migrations/         Alembic (async template)
├── app/
│   ├── models/user.py
│   ├── schemas/            user.py, auth.py
│   ├── services/auth.py    registration, lookup, authentication
│   └── routes/auth.py
└── utils/enums.py          TokenType, UserRole
```

## Setup

```bash
cd backend
uv sync
cp .env.example .env
uv run alembic -c database/alembic.ini upgrade head
uv run fastapi dev main.py
```

Docs: http://127.0.0.1:8000/docs

## Endpoints

| Method | Path                 | Auth   | Description                        |
| ------ | -------------------- | ------ | ---------------------------------- |
| POST   | `/api/auth/register` | –      | Create an account, returns tokens  |
| POST   | `/api/auth/login`    | –      | Email + password, returns tokens   |
| POST   | `/api/auth/refresh`  | –      | Refresh token, returns a new pair  |
| GET    | `/api/auth/me`       | Bearer | Current user                       |
| GET    | `/health`            | –      | Liveness probe                     |

Access tokens live 30 minutes, refresh tokens 7 days (both configurable). Both are
JWTs carrying `sub`, `type`, `jti`, `iat`, `exp`; the `type` claim keeps a refresh
token from being accepted as an access token and vice versa.

Refresh tokens are stateless — a leaked one stays valid until it expires. Add a
`jti` denylist table if you need logout-everywhere or revocation.

## Migrations

Alembic lives under `database/`, so every command needs `-c`. Run them from
`backend/`, which is where the SQLite path in `.env` resolves from.

```bash
uv run alembic -c database/alembic.ini revision --autogenerate -m "message"
uv run alembic -c database/alembic.ini upgrade head
uv run alembic -c database/alembic.ini downgrade -1
```

`database/migrations/env.py` reads `DATABASE_URL` from settings and runs with
`render_as_batch=True`, which SQLite needs for `ALTER TABLE`. New models must be
imported in `app/models/__init__.py` or autogenerate will not see them.

## Enums

`utils/enums.py` holds the shared `StrEnum`s. `TokenType` is the JWT `type` claim
that keeps access and refresh tokens from being used in each other's place.
`UserRole` is the `users.role` column, stored as a VARCHAR and surfaced in the
OpenAPI schema as a string enum; `require_role(UserRole.ADMIN)` builds a
dependency from it and `CurrentAdmin` is the ready-made alias.
