# BookMe — Office Reservations

Modern web app for booking office desks and rooms with approvals, interactive SVG floor plan, and role‑based access.

## Setup instructions (in short)

1) Prereqs
- Node 20.x and npm (or Bun 1.0+)
- Git

2) Clone
```
git clone https://github.com/whos-gabi/pu-erh.git
cd pu-erh
```

3) Configure env (frontend)
```
cd frontend
cp .env.sample .env
# required
NEXT_PUBLIC_API_BASE_URL=https://api.desepticon.qzz.io/
```

4) Install deps
```
# with npm
npm install
# or with bun
bun i
```

5) Run dev
```
npm run dev
# or
bun run dev
```

App runs at http://localhost:3000

## Tech stack used

- Next.js 16 (App Router, Server/Client Components)
- React 19
- TypeScript 5
- Tailwind CSS v4
- shadcn/ui (Radix primitives + headless UI)
- NextAuth (credentials) for login
- SVG interactivity (DOM APIs) with custom pan/zoom
- Vercel for hosting
- Dockerised PostgreSQL
- Dockerised Django API

## Backend setup (in short)

1) Prereqs
- Docker + Docker Compose (recommended), or Python 3.11+ and PostgreSQL if running locally

2) Environment
```
cd backend
cp .env.example .env
# Update DB settings if needed, e.g.:
# POSTGRES_DB=bookme
# POSTGRES_USER=bookme
# POSTGRES_PASSWORD=bookme
# POSTGRES_HOST=db
# POSTGRES_PORT=5432
# DJANGO_SECRET_KEY=change-me
# DJANGO_DEBUG=True
```

3) Run with Docker (recommended)
```
# from repo root
docker compose up -d db
docker compose up -d backend

# first-time setup (inside the backend container)
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser  # optional
```
API will be available at http://localhost:8000/ (adjust if you mapped a different port).

4) Run locally (without Docker)
```
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

5) (Optional) Seed / analytics simulation
```
# Example simulation to (re)compute monthly popularity stats
python services/databrics.py
```
This simulates the Databricks monthly pipeline that populates the item popularity table used by the `/api/item-occupancy-stats/stats/` route.

## Backend overview

- Framework: Django + Django REST Framework
- DB: PostgreSQL (Dockerized)
- Auth: JWT-based login endpoint exposed and consumed by the frontend
- API proxy: Next.js API routes proxy requests from the browser to the external API to avoid CORS
- Key endpoints used by the frontend:
  - `POST /api/auth/login/` — credentials login, returns access/refresh JWT
  - `GET /api/users/{id}/` — user profile (proxied by frontend)
  - `GET /api/availability/check/?date=YYYY-MM-DD&user_id={id}` — seats/rooms availability for date
  - `POST /api/appointments/` — create appointment for items (desks, etc.)
  - `POST /api/requests/` — submit approval requests for rooms/areas
  - `GET /api/items/` — list items (names and ids)
  - `GET /api/item-occupancy-stats/stats/?item_id={id}` — popularity stats for an item

### Popularity stats (Databricks monthly job - simulated)

There is a dedicated route that fetches data from a table maintained by an external Databricks pipeline. The pipeline runs monthly to compute statistical popularity of items per weekday (0–100%) by aggregating historical occupancy signals.

- Source table: item occupancy statistics (materialized monthly by Databricks)
- Public API: `GET /api/item-occupancy-stats/stats/?item_id={id}`
- Frontend usage: when selecting any item on the map, the UI fetches the stats and renders a compact bar chart (Mo–Su) showing average popularity for 08:00–20:00.

## Demo credentials

- Admin
  - usr: `super123`
  - pwd: `super123`

- Users (pwd for all: `parola123`)
  - `garcia0`
  - `whitehead1`
  - `williams2`
  - `garcia3`
  - `contreras4`
  - `ramirez5`
  - `miranda6`
  - `fuller7`
  - `frank8`
  - `jackson9`

## Hosted on

- Web: https://book-me-five.vercel.app/
- API docs: https://api.desepticon.qzz.io/api/docs/#/

Notes
- Admin sees Dashboard. Members see Account and Reservations.
- Interactive SVG on Reserve supports hover, select, approval flows, and availability overlays.
- Environment variable `NEXT_PUBLIC_API_BASE_URL` configures the API base for the frontend.
