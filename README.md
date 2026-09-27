# DATAM storefront

Russian-language fashion storefront. The frontend is served by Nginx at `http://localhost`; Compose publishes port 80 on localhost only. Nginx forwards `/api` and `/media` to FastAPI and `/pgadmin` to pgAdmin. PostgreSQL and pgAdmin are available only inside the Compose network.

## Run

1. Copy `.env.example` to `.env` if you do not already have an environment file. Set long random values for `SECRET_KEY`, `POSTGRES_PASSWORD`, and `PGADMIN_DEFAULT_PASSWORD`. Use a URL-safe PostgreSQL password because Compose embeds it in the backend database URL.
2. Run `make up`.
3. Run `make seed` to populate the current PostgreSQL database.
4. Open `http://localhost` for the store, `http://localhost/admin` for the administrator interface, and `http://localhost/pgadmin` for pgAdmin.

Sign in to pgAdmin with `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD`. The DATAM PostgreSQL server is preconfigured there; enter `POSTGRES_PASSWORD` when connecting to it. On a fresh database, register an account in the store, then grant it admin access in pgAdmin's Query Tool with `UPDATE users SET role = 'admin' WHERE email = 'your@email.com';`. Sign in to `/admin` with that account. The backend applies Alembic migrations on startup. `make seed` is idempotent and runs only when requested. Set `COOKIE_SECURE=true` when serving the site over HTTPS.

The store uses the dedicated `datam` database in PostgreSQL, persisted in `postgres-data`. pgAdmin keeps its own settings in `pgadmin-data`. Existing data from earlier storage is not imported automatically. `make reset` removes all Compose volumes.

## Code layout

- `frontend/src`: Feature Sliced Design layers (`app`, `pages`, `widgets`, `features`, `entities`, `shared`). All customer API calls use same-origin `/api` requests with cookies.
- `backend/app/routes/commerce`: cart, favorites, and order routes.
- `backend/app/services/commerce`: corresponding business logic, including guest merge and stock checked order creation.
- `backend/seed.py`: demo categories, products, variants, and image references.

## Checks

Run `npm run lint` and `npm run build` in `frontend/`. The backend flow test requires `TEST_DATABASE_URL` pointing to a disposable PostgreSQL database whose name ends in `_test`.
