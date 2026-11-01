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
![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)
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
- [Demo Data](#demo-data)
- [Testing](#testing)
- [API Reference](#api-reference)
- [Data Model](#data-model)
- [Security](#security)
- [Roadmap](#roadmap)
- [License](#license)

---

## Overview

ShiftMaster AI turns employee availability, shift preferences and labor rules into a ready-to-publish schedule. Managers plan, review and analyze schedules in the **web dashboard**. Employees use the **mobile app** to see their week, request leave and set their preferences, even when they are offline. A separate **Security AI** module scans source code for vulnerabilities using a hybrid rule + ML detection engine.

| Client | Audience | Purpose |
| --- | --- | --- |
| **Web dashboard** (Next.js) | Admins, managers | Employees, shifts, rules, AI optimization, analytics, security scanning |
| **Mobile app** (Flutter) | Employees | Weekly shifts, leave requests, shift preferences, notifications, profile |
| **REST API** (FastAPI) | Both clients | Auth, scheduling engine, business rules, real-time events, health and metrics |

The web dashboard and the mobile app share the same branding, color palette (`#1E3A5F`) and terminology (Morning / Day / Evening / Night shifts), so managers and employees see one product.

---

## Screenshots

### Web

| | |
| --- | --- |
| <img src="docs/screenshots/dashboard.png" alt="Dashboard"><br>**Dashboard:** KPIs, shifts by weekday, department mix, six-month trend and upcoming shifts, all computed from live data. | <img src="docs/screenshots/ai-optimization.png" alt="AI optimization"><br>**AI optimization:** a full week for 204 employees, with its score, coverage, preference match and fairness. |
| <img src="docs/screenshots/employees.png" alt="Employees"><br>**Employees:** contract limits, roles and each person’s preferred shift and day off. | <img src="docs/screenshots/shifts.png" alt="Shifts"><br>**Shifts:** list and calendar views with conflict detection. |
| <img src="docs/screenshots/rules.png" alt="Shift rules"><br>**Shift rules:** staffing requirements per department, role and day. | <img src="docs/screenshots/security-dashboard.png" alt="Security AI dashboard"><br>**Security AI dashboard:** statistics from real scans, plus the engine’s status. |
| <img src="docs/screenshots/security-scan.png" alt="Vulnerability scanner"><br>**Vulnerability scanner:** findings with CWE/OWASP mapping, line numbers and fixes. | <img src="docs/screenshots/security-rules.png" alt="Detection rules"><br>**Detection rules:** the rule set loaded in the engine. |

### Sign-in and onboarding

| | |
| --- | --- |
| <img src="docs/screenshots/login.png" alt="Sign in"> | <img src="docs/screenshots/register.png" alt="Create account"> |

<details>
<summary><b>Full landing page and mobile view</b></summary>

<p align="center">
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

### Analytics and real-time updates
- A dashboard computed on the server from real shift data, filterable by week or month.
- Server-Sent Events (`/events/stream`) with a polling fallback.
- An in-app notification center, plus push notifications on mobile.

### Security AI module
- A **hybrid detector**: a deterministic regex/AST rule engine, an optional TensorFlow model, and a fusion layer that combines the two (Conservative / Balanced / Aggressive). Critical rule matches are never suppressed.
- 13 rules mapped to OWASP Top 10 and CWE, covering SQL and command injection, hardcoded secrets, insecure deserialization, weak cryptography, path traversal and more.
- Scans are stored in the database, which feeds the Security dashboard.
- When no trained model is loaded, scans run in rule-based mode, and the UI says so instead of showing model metrics.
- A training toolkit (stratified/temporal splitting, SMOTE, focal loss, evaluation, continuous learning) and a MindSpore/Ascend migration plan are included as design references.

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
        S["Security AI<br/>Hybrid Rule + ML Detector"]
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
    R --> S --> DB
    E -. "real-time" .-> W
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
| **Security AI** | Regex/AST rule engine, NumPy, optional TensorFlow model, MindSpore migration templates |
| **Web** | Next.js 16 (App Router), React 19, TypeScript, Ant Design 6, Tailwind CSS 4, Zustand, Axios, Recharts, Day.js, SheetJS |
| **Mobile** | Flutter / Dart, Provider, Dio, go_router, sqflite, flutter_secure_storage, connectivity_plus, Firebase Messaging |
| **Quality** | pytest, ESLint, TypeScript strict mode |

---

## Repository Structure

```text
shift-planning-application/
├── backend/                      # FastAPI service
│   ├── alembic/versions/         # 001 schema · 002 leave · 003 indexes · 004 preferences · 005 security scans
│   ├── app/
│   │   ├── domain/services/      # schedule_optimizer.py, rule engine, leave, audit
│   │   ├── middleware/           # Rate limiting, logging, security headers
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── routers/              # REST endpoints (/api/v1)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── scripts/              # seed_demo_data.py + synthetic dataset
│   │   ├── security_ai/          # Hybrid vulnerability detection engine and ML toolkit
│   │   ├── tasks/                # Celery background jobs
│   │   └── utils/                # Hashing and JWT helpers
│   └── tests/                    # Optimizer unit tests
├── web/ai-shiftmaster-web/       # Next.js dashboard and landing page
│   └── app/
│       ├── landing/  login/  register/
│       ├── dashboard/  employees/  shifts/  rules/  ai-optimization/
│       ├── security/             # Dashboard, scanner, rules, training and migration previews
│       └── components/  lib/  store/  theme/  types/
├── employee_shift_mobile/        # Flutter employee app
│   └── lib/  core/  data/  providers/  services/  presentation/
├── docs/                         # Screenshots and extended architecture notes
└── LICENSE
```

---

## Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **PostgreSQL** 14+
- **Flutter SDK** 3.x (only for the mobile app)
- **Redis** (optional, only for Celery background jobs)

### 1. Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate   |   macOS/Linux: source venv/bin/activate
pip install -r requirements.txt          # add -r requirements-ml.txt for the optional TensorFlow layer

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

## Demo Data

All people in the demo workforce are **fictional**. [`seed_demo_data.py`](backend/app/scripts/seed_demo_data.py) loads 200 synthetic employees from [`demo_employees.json`](backend/app/scripts/data/demo_employees.json). Names are random combinations of common first and last names, and every email uses `example.com`. Each employee has a role, a department, a preferred shift, a weekly day off and a work model. The script is idempotent: running it again updates the existing records.

On first startup, the backend also creates these development accounts. Change or remove them before you deploy.

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@example.com` | `admin123` |
| Manager | `manager@example.com` | `manager123` |
| Employee | `employee@example.com` | `employee123` |

---

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests -q
```

The optimizer suite covers one shift per day, weekly hour caps, operating days, days off, minimum rest, the use of existing shifts, the effect of preferences, understaffing warnings and deterministic output.

---

## API Reference

All business endpoints are served under `/api/v1`. When the backend is running, the full contract is available at `/docs`.

| Area | Endpoints |
| --- | --- |
| **Auth** | `POST /auth/login` · `POST /auth/register` · `POST /auth/refresh` · `POST /auth/logout` · `GET /auth/me` |
| **Dashboard** | `GET /dashboard/summary?start_date&end_date` |
| **Employees** | `GET/POST /employees` · `GET/PUT/DELETE /employees/{id}` |
| **Departments** | `GET/POST /departments` · `GET/PUT/DELETE /departments/{id}` |
| **Shifts** | `GET/POST /shifts` · `GET/PUT/DELETE /shifts/{id}` · `GET /shifts/conflicts` · `POST /shifts/bulk` |
| **Shifts v2** | `GET /shifts/v2/validate/{employee_id}` · `POST /shifts/v2/optimized` · `GET /shifts/v2/recommendations/{department_id}` · `PUT /shifts/v2/{id}/soft-delete` · `GET /shifts/v2/audit/{id}` |
| **Shift rules** | `GET/POST /rules` · `GET/PUT/DELETE /rules/{id}` |
| **AI optimization** | `POST /ai/optimize` (preview) · `POST /ai/apply` (save) |
| **Leave requests** | `GET/POST /leave-requests` · `GET /leave-requests/my` · `DELETE /leave-requests/{id}` · `/leave-requests/v2/*` (balance, decide, pending, analytics) |
| **Notifications** | `GET /notifications` · `PUT /notifications/{id}/read` · `PUT /notifications/read-all` · `DELETE /notifications/{id}` |
| **Events** | `GET /events/stream` (SSE) · `GET /events/poll` · `GET /events/stats` |
| **Security AI** | `POST/GET /security/scans` · `GET /security/dashboard/stats` · `GET /security/engine/rules` · `POST /security/scan/code` · `POST /security/scan/file` · `POST /security/scan/project` · `POST /security/quick-fix` |
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
    USER ||--o{ SECURITY_SCAN : runs
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
| `security_scans` | Stored Security AI scans and their findings |
| `audit_logs` | Change history for compliance |

The schema is versioned with Alembic. There are five migrations, and they are tested both upgrading and downgrading.

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

- [ ] Ship trained weights for the Security AI model, and connect the **ML training** and **MindSpore migration** pages, which currently show labeled sample data.
- [ ] Add API integration tests and Playwright end-to-end tests, and run them in a CI pipeline.
- [ ] Persist mobile preference changes through the API (the backend field already exists).
- [ ] Add Docker Compose for one-command local setup.
- [ ] Add multi-tenant workspaces for self-service company sign-up.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
