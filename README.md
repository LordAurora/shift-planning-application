<div align="center">

# ShiftMaster AI

**AI-assisted workforce scheduling: a constraint-aware optimizer, a web dashboard for managers and an offline-first mobile app for employees, on one FastAPI backend.**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-4169E1?logo=postgresql&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?logo=flutter&logoColor=white)
[![CI](https://github.com/LordAurora/shift-planning-application/actions/workflows/ci.yml/badge.svg)](https://github.com/LordAurora/shift-planning-application/actions/workflows/ci.yml)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

<img src="docs/screenshots/landing-hero.png" alt="ShiftMaster AI landing page" width="100%">

</div>

---

## Table of Contents

- [Overview](#overview)
- [Screenshots](#screenshots)
- [Key Features](#key-features)
- [How the Optimizer Works](#how-the-optimizer-works)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Run with Docker](#run-with-docker)
- [Demo Data](#demo-data)
- [Testing and CI](#testing-and-ci)
- [API Reference](#api-reference)
- [Data Model](#data-model)
- [Security](#security)
- [Roadmap](#roadmap)
- [License](#license)

---

## Overview

ShiftMaster AI turns employee availability, shift preferences and labor rules into a ready-to-publish schedule. Managers plan, review and analyze schedules in the **web dashboard**. Employees use the **mobile app** to see their week, request leave and set their preferences, even when they are offline.

| Client | Audience | Purpose |
| --- | --- | --- |
| **Web dashboard** (Next.js) | Admins, managers | Employees, shifts, rules, AI optimization, analytics |
| **Mobile app** (Flutter) | Employees | Weekly shifts, leave requests, shift preferences, notifications, profile |
| **REST API** (FastAPI) | Both clients | Auth, scheduling engine, business rules, notifications, health and metrics |

The web dashboard and the mobile app share the same branding, color palette (`#1E3A5F`) and terminology (Morning / Day / Evening / Night shifts), so managers and employees see one product.

---

## Screenshots

### Web

| | |
| --- | --- |
| <img src="docs/screenshots/dashboard.png" alt="Dashboard"><br>**Dashboard:** KPIs, shifts by weekday, department mix, six-month trend and upcoming shifts, all computed from live data. | <img src="docs/screenshots/ai-optimization.png" alt="AI optimization"><br>**AI optimization:** a full week for 204 employees, with its score, coverage, preference match and fairness. |
| <img src="docs/screenshots/employees.png" alt="Employees"><br>**Employees:** contract limits, roles and each person’s preferred shift and day off. | <img src="docs/screenshots/shifts.png" alt="Shifts"><br>**Shifts:** list and calendar views with conflict detection. |
| <img src="docs/screenshots/rules.png" alt="Shift rules"><br>**Shift rules:** staffing requirements per department, role and day. | <img src="docs/screenshots/login.png" alt="Sign in"><br>**Sign in:** split-screen SaaS layout shared with the sign-up page. |

<details>
<summary><b>Sign-up, full landing page and mobile view</b></summary>

<p align="center">
  <img src="docs/screenshots/register.png" alt="Create account" width="80%">
  <img src="docs/screenshots/landing-full.png" alt="Full landing page" width="80%">
  <img src="docs/screenshots/landing-mobile.png" alt="Landing page on mobile" width="300">
</p>

</details>

---

## Key Features

### Scheduling
- **Constraint-aware optimizer.** Hard rules are never broken: weekly hour caps, minimum rest between shifts, maximum consecutive days, availability and weekly days off. Within those rules, candidates are ranked by preferred shift and workload balance.
- **Explainable results.** Every run reports an optimization score, coverage, preference match, fairness and its warnings (understaffed slots, overtime). Nothing is saved until the manager confirms.
- **Works with existing plans.** Shifts already in the period count towards hours and rest periods, and fill their slots. Re-running a week never double-books anyone.
- **Configurable.** Shift types, operating days or 24/7 mode, staffing ranges, overtime and the preference weight can all be adjusted.
- **Exports** to Excel, CSV, print view and clipboard.

### Workforce management
- Employee and department management with weekly hour and overtime limits.
- Employee preferences (preferred shift, weekly day off, work model), shared between web and mobile.
- Shift rules per department and role.
- Leave requests with balance tracking, an approval workflow and analytics.
- A shift audit trail.

### Analytics and notifications
- A dashboard computed on the server from real shift data, filterable by week or month.
- An event-stream API (`/events/stream`, Server-Sent Events with a polling fallback) for clients that need live updates.
- An in-app notification center, plus push notifications on mobile.

### Mobile app (Flutter)
- Home screen with the current and next shift, a weekly schedule, leave requests, preferences, notifications and profile.
- **Offline-first:** a local SQLite cache and a queue of pending changes, synced every 5 minutes with retries.
- Secure token storage and push notifications.

### Platform
- JWT authentication with role-based access control (**Admin / Manager / Employee**).
- Rate limiting, structured logging and security-header middleware.
- Health, readiness and liveness probes, plus Prometheus-compatible `/metrics`.
- Celery + Redis background jobs (notifications, maintenance).

---

## How the Optimizer Works

The optimizer lives in [`backend/app/domain/services/schedule_optimizer.py`](backend/app/domain/services/schedule_optimizer.py). It is plain Python with no framework or database dependencies, which makes it easy to test.

```mermaid
flowchart LR
    A["Employees<br/>limits · availability · preferences"] --> C
    B["Existing shifts<br/>in the period"] --> C
    S["Settings<br/>shift types · days · limits · weights"] --> C
    C{"For each day × shift type × department"}
    C --> D["Filter by hard constraints<br/>1 shift/day · weekly cap · 11h rest<br/>consecutive days · day off · availability"]
    D --> E["Score candidates<br/>w × preference + (1 − w) × workload balance"]
    E --> F["Fill the remaining demand<br/>with the top-ranked candidates"]
    F --> G["Metrics and warnings<br/>coverage · preference match · fairness"]
```

- **Demand** per slot comes from team size and contract hours, and is clamped to the configured minimum and maximum staffing.
- **Determinism:** the same input always produces the same schedule. A stable tie-breaker rotates people across days, so results are reproducible and easy to review.
- **Score** = 45% coverage + 30% preference match + 25% fairness (fairness is 1 minus the coefficient of variation of hours). When preferences are switched off, the score is 60% coverage + 40% fairness.
- On the 200-person demo workforce, a full week is generated in about 2 seconds, with 100% coverage and over 99% preference match.

---

## Architecture

```mermaid
flowchart LR
    subgraph Clients
        W["Web Dashboard<br/>Next.js · React · Ant Design"]
        M["Mobile App<br/>Flutter · Provider · SQLite"]
    end

    subgraph Backend["FastAPI Backend"]
        MW["Middleware<br/>JWT · Rate limit · Logging"]
        R["REST Routers<br/>/api/v1/*"]
        D["Domain Services<br/>Optimizer · Rule Engine · Leave · Audit"]
        E["SSE Event Stream"]
    end

    subgraph Infra["Infrastructure"]
        DB[("PostgreSQL")]
        Q[("Redis")]
        C["Celery Workers"]
        F["Push Notifications"]
    end

    W -- "HTTPS / JSON" --> MW
    M -- "HTTPS / JSON" --> MW
    MW --> R --> D --> DB
    D --> Q --> C
    C --> F -. "push" .-> M
```

### Optimization flow

```mermaid
sequenceDiagram
    participant Mgr as Manager (Web)
    participant API as FastAPI
    participant Opt as ScheduleOptimizer
    participant DB as PostgreSQL

    Mgr->>API: POST /api/v1/ai/optimize (period, departments, settings)
    API->>DB: Load employees, preferences and existing shifts
    API->>Opt: optimize(employees, period, existing)
    Opt-->>API: Assignments + score + metrics + warnings
    API-->>Mgr: Preview (nothing saved yet)
    Mgr->>API: POST /api/v1/ai/apply
    API->>DB: Persist the schedule
```

---

## Tech Stack

| Layer | Technologies |
| --- | --- |
| **Backend** | Python, FastAPI, Uvicorn, SQLAlchemy 2, Alembic, Pydantic v2, psycopg 3 |
| **Auth & security** | JWT (python-jose), bcrypt (passlib), RBAC, rate-limiting middleware |
| **Async / jobs** | Celery, Redis, Server-Sent Events |
| **Database** | PostgreSQL (GaussDB-compatible) |
| **Web** | Next.js 16 (App Router), React 19, TypeScript, Ant Design 6, Tailwind CSS 4, Zustand, Axios, Recharts, Day.js, SheetJS |
| **Mobile** | Flutter / Dart, Provider, Dio, go_router, sqflite, flutter_secure_storage, connectivity_plus, Firebase Messaging |
| **Quality** | pytest (unit + API tests), ESLint, TypeScript strict mode, GitHub Actions |
| **Delivery** | Docker, Docker Compose |

---

## Repository Structure

```text
shift-planning-application/
├── backend/                      # FastAPI service
│   ├── alembic/versions/         # 001 schema · 002 leave · 003 indexes · 004 preferences
│   ├── app/
│   │   ├── domain/services/      # schedule_optimizer.py, rule engine, leave, audit
│   │   ├── middleware/           # Rate limiting, logging, security headers
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── routers/              # REST endpoints (/api/v1)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── scripts/              # seed_demo_data.py + synthetic dataset
│   │   ├── tasks/                # Celery background jobs
│   │   └── utils/                # Hashing and JWT helpers
│   ├── tests/                    # Optimizer unit tests and API tests
│   └── Dockerfile
├── web/ai-shiftmaster-web/       # Next.js dashboard and landing page
│   └── app/
│       ├── landing/  login/  register/
│       ├── dashboard/  employees/  shifts/  rules/  ai-optimization/
│       └── components/  lib/  store/  theme/  types/
├── employee_shift_mobile/        # Flutter employee app
│   └── lib/  core/  data/  providers/  services/  presentation/
├── docs/                         # Screenshots and extended architecture notes
├── docker-compose.yml            # PostgreSQL + API + web in one command
├── .github/workflows/ci.yml      # Tests, migrations, lint, build, Docker
└── LICENSE
```

---

## Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 20.9+ (required by Next.js 16)
- **PostgreSQL** 14+
- **Flutter SDK** 3.x (only for the mobile app)
- **Redis** (optional, only for Celery background jobs)

### 1. Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate   |   macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env                     # set DATABASE_URL and SECRET_KEY
alembic upgrade head                     # create the schema
python -m app.scripts.seed_demo_data     # optional: 200 synthetic employees
uvicorn app.main:app --reload
```

The API runs at **http://localhost:8000**. Interactive docs are at `/docs` (Swagger) and `/redoc`.

> **Existing database created before migrations?** If your tables were created by an older version (via `create_all`), run `alembic stamp 002_add_leave_requests` once, then `alembic upgrade head`.

<details>
<summary>Environment variables</summary>

| Variable | Description | Example |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string (the psycopg 3 driver is selected automatically) | `postgresql://postgres:password@localhost:5432/shiftmaster` |
| `SECRET_KEY` | JWT signing key. Use a long random value. | `openssl rand -hex 32` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `1440` |
| `CORS_ORIGINS` | Allowed origins, comma-separated | `http://localhost:3000` |
| `ENVIRONMENT` / `DEBUG` | Runtime mode | `development` / `True` |

</details>

### 2. Web dashboard

```bash
cd web/ai-shiftmaster-web
npm install
cp .env.example .env.local         # NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
npm run dev
```

Open **http://localhost:3000**. Visitors see the landing page; signed-in users go to the dashboard.

### 3. Mobile app

```bash
cd employee_shift_mobile
flutter pub get
flutter run
```

> On an Android emulator, the app reaches the backend on the host machine at `http://10.0.2.2:8000` (configured in `lib/core/config/app_config.dart`).

---

## Run with Docker

```bash
docker compose up --build
```

This starts PostgreSQL, the API (it runs the migrations and loads the demo workforce on startup) and the web dashboard:

- Web: **http://localhost:3000**. Sign in with `admin@example.com` / `admin123`.
- API docs: **http://localhost:8000/docs**

Set `SECRET_KEY` in your environment before using the stack for anything other than local development.

---

## Demo Data

All people in the demo workforce are **fictional**. [`seed_demo_data.py`](backend/app/scripts/seed_demo_data.py) loads 200 synthetic employees from [`demo_employees.json`](backend/app/scripts/data/demo_employees.json). Names are random combinations of common first and last names, and every email uses `example.com`. Each employee has a role, a department, a preferred shift, a weekly day off and a work model. The script is idempotent: running it again updates the existing records.

On first startup, the backend also creates these development accounts. Change or remove them before you deploy.

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@example.com` | `admin123` |
| Manager | `manager@example.com` | `manager123` |
| Employee | `employee@example.com` | `employee123` |

---

## Testing and CI

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests -q
```

There are 23 tests in two groups:

- **Optimizer unit tests** cover one shift per day, weekly hour caps, operating days, days off, minimum rest, existing shifts (counted towards hours and slots), the effect of preferences, understaffing warnings and deterministic output.
- **API tests** run the real FastAPI app against a temporary SQLite database. They cover sign-in, role protection, the sign-up role rules, employees and preferences, shift rules, and the full flow of optimizing, saving and re-running a week. They never touch the database configured in `.env`.

Every push runs the [CI pipeline](.github/workflows/ci.yml):

| Job | What it checks |
| --- | --- |
| Backend · tests | The full pytest suite |
| Backend · migrations | `alembic upgrade head`, `alembic check` (models match migrations), a downgrade/upgrade round trip and an idempotent seed, all on PostgreSQL 16 |
| Web | ESLint, the TypeScript type check and a production `next build` |
| Docker | Building the images with `docker compose build` |

---

## API Reference

All business endpoints are served under `/api/v1`. When the backend is running, the full contract is available at `/docs`.

| Area | Endpoints |
| --- | --- |
| **Auth** | `POST /auth/login` · `POST /auth/register` · `POST /auth/refresh` · `POST /auth/logout` · `GET /auth/me` |
| **Dashboard** | `GET /dashboard/summary?start_date&end_date` |
| **Employees** | `GET/POST /employees` · `GET/PUT/DELETE /employees/{id}` · `GET/PUT /employees/me/preferences` |
| **Departments** | `GET/POST /departments` · `GET/PUT/DELETE /departments/{id}` |
| **Shifts** | `GET/POST /shifts` · `GET/PUT/DELETE /shifts/{id}` · `GET /shifts/conflicts` · `POST /shifts/bulk` |
| **Shifts v2** | `GET /shifts/v2/validate/{employee_id}` · `POST /shifts/v2/optimized` · `GET /shifts/v2/recommendations/{department_id}` · `PUT /shifts/v2/{id}/soft-delete` · `GET /shifts/v2/audit/{id}` |
| **Shift rules** | `GET/POST /rules` · `GET/PUT/DELETE /rules/{id}` |
| **AI optimization** | `POST /ai/optimize` (preview) · `POST /ai/apply` (save) |
| **Leave requests** | `GET/POST /leave-requests` · `GET /leave-requests/my` · `DELETE /leave-requests/{id}` · `/leave-requests/v2/*` (balance, decide, pending, analytics) |
| **Notifications** | `GET /notifications` · `PUT /notifications/{id}/read` · `PUT /notifications/read-all` · `DELETE /notifications/{id}` |
| **Events** | `GET /events/stream` (SSE) · `GET /events/poll` · `GET /events/stats` |
| **Health** (root) | `GET /health` · `/health/ready` · `/health/live` · `/health/detailed` · `/metrics` · `/metrics/json` · `/info` |

<details>
<summary>Example: optimize a week</summary>

```http
POST /api/v1/ai/optimize
Authorization: Bearer <token>
Content-Type: application/json

{
  "start_date": "2026-11-30",
  "end_date": "2026-12-06",
  "settings": {
    "shift_types": ["morning", "day", "afternoon"],
    "operating_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "max_hours_per_week": 45,
    "min_rest_hours": 11,
    "consider_preferences": true,
    "preference_weight": 70
  }
}
```

The response includes `shifts` (each with `shift_type` and a `preferred` flag), `conflicts`, `optimization_score` and `metrics` (`coverage`, `preference_match`, `fairness`, `total_hours`, `employees_scheduled`).

</details>

---

## Data Model

```mermaid
erDiagram
    DEPARTMENT ||--o{ EMPLOYEE : employs
    DEPARTMENT ||--o{ SHIFT : schedules
    DEPARTMENT ||--o{ SHIFT_RULE : defines
    EMPLOYEE ||--o{ SHIFT : "is assigned"
    USER ||--o{ LEAVE_REQUEST : submits
    USER ||--o{ NOTIFICATION : receives
    USER ||--o{ AUDIT_LOG : performs
```

| Table | Description |
| --- | --- |
| `users` | Login accounts and roles |
| `departments` | Organizational units |
| `employees` | Profiles, availability, weekly and overtime limits, and `preferences` (preferred shift, day off, work model) |
| `shifts` | Scheduled shifts |
| `shift_rules` | Staffing requirements per department, role, day and time range |
| `leave_requests` | Leave applications and approval state |
| `notifications` | User notifications |
| `audit_logs` | Change history for compliance |

The schema is versioned with Alembic. There are four migrations, and they are tested both upgrading and downgrading.

---

## Security

- Passwords are hashed with **bcrypt**. Tokens are signed JWTs with a configurable lifetime.
- **Self-service sign-up cannot choose a role.** The very first account becomes the administrator; every later sign-up is an employee. Elevated roles are granted by an administrator.
- Role-based authorization is enforced on the API and, through middleware, on Next.js routes.
- Request rate limiting and security headers are applied by middleware.
- Secrets are read only from environment variables. `.env` files are git-ignored, and `.env.example` documents the required keys.
- Pydantic validates every request body.

---

## Roadmap

- [x] Constraint-aware optimizer with explainable metrics
- [x] Live dashboard, shift rules and sign-up connected to the API
- [x] Mobile preferences saved through the API and used by the optimizer
- [x] Unit tests, API tests and a CI pipeline
- [x] Docker Compose setup
- [ ] Browser end-to-end tests (Playwright) and a Flutter build in CI
- [ ] Multi-tenant workspaces, so each company that signs up gets its own data

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
