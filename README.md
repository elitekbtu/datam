# DATAM storefront

Russian-language fashion storefront. The frontend is served by Nginx at `http://localhost`; Compose publishes only port 80. Nginx also forwards `/api` and `/media` to the internal FastAPI service. There is no separate frontend port in the Compose stack.

## Run

1. Copy `.env.example` to `.env` if you do not already have an environment file. Set a long random `SECRET_KEY`.
2. Run `make up`.
3. Open `http://localhost`.

The backend applies Alembic migrations and seeds the demo catalog on startup. The seed is idempotent. Set `COOKIE_SECURE=true` when serving the site over HTTPS.

## Code layout

- `frontend/src`: Feature Sliced Design layers (`app`, `pages`, `widgets`, `features`, `entities`, `shared`). All customer API calls use same-origin `/api` requests with cookies.
- `backend/app/routes/commerce`: cart, favorites, and order routes.
- `backend/app/services/commerce`: corresponding business logic, including guest merge and stock checked order creation.
- `backend/seed.py`: demo categories, products, variants, and image references.

## Checks

Run `npm run lint` and `npm run build` in `frontend/`. Run `./.venv/bin/python -m unittest discover -s tests -v` in `backend/` after installing backend dependencies.
