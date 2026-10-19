<div align="center">

# ShiftMaster AI

**AI-assisted workforce scheduling platform: web dashboard, employee mobile app and a security analysis module, all on one FastAPI backend.**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-4169E1?logo=postgresql&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?logo=flutter&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Screenshots](#screenshots)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Data Model](#data-model)
- [Security](#security)
- [Roadmap](#roadmap)
- [License](#license)

---

## Overview

ShiftMaster AI helps organizations plan employee shifts while staying inside labor rules, availability constraints and fairness goals. Managers build and optimize schedules from the **web dashboard**. Employees check their shifts, submit leave requests and set shift preferences from the **mobile app**, which also works offline. A separate **Security AI** module scans source code for vulnerabilities with a hybrid rule + machine-learning engine.

| Client | Audience | Purpose |
| --- | --- | --- |
| **Web dashboard** (Next.js) | Admins, managers | Employees, departments, shifts, rules, AI optimization, analytics, security scanning |
| **Mobile app** (Flutter) | Employees | Weekly shifts, leave requests, shift preferences, notifications, profile |
| **REST API** (FastAPI) | Both clients | Auth, business rules, optimization, real-time events, health and metrics |

---

## Screenshots

<p align="center">
  <img src="docs/screenshots/landing.png" alt="Landing page" width="100%">
</p>

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/dashboard.png" alt="Dashboard"><p align="center"><b>Dashboard</b>: workforce KPIs, weekly shift distribution and department breakdown</p></td>
    <td width="50%"><img src="docs/screenshots/shifts.png" alt="Shift management"><p align="center"><b>Shift management</b>: list and calendar views, filtered by date range and department</p></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/ai-optimization.png" alt="AI optimization"><p align="center"><b>AI optimization</b>: generate a schedule that takes employee preferences into account</p></td>
    <td><img src="docs/screenshots/employees.png" alt="Employee management"><p align="center"><b>Employees</b>: weekly and overtime limits, plus availability</p></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/rules.png" alt="Shift rules"><p align="center"><b>Shift rules</b>: staffing requirements per department and day</p></td>
    <td><img src="docs/screenshots/login.png" alt="Login"><p align="center"><b>Login</b>: JWT-based authentication</p></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/security-dashboard.png" alt="Security AI dashboard"><p align="center"><b>Security AI dashboard</b>: severity distribution and detection sources</p></td>
    <td><img src="docs/screenshots/security-scan.png" alt="Vulnerability scanner"><p align="center"><b>Vulnerability scanner</b>: hybrid rule + ML code analysis</p></td>
  </tr>
</table>

---

## Key Features

### Scheduling & Optimization
- **AI shift optimization** that scores each candidate employee on availability, workload balance and skill match, with selectable strategies: balanced, minimize overtime, maximize preferences, cost-effective and emergency fill.
- **Rule engine** that checks labor law limits, overtime caps and minimum rest periods, with severity levels from warning to blocking.
- **Conflict detection** for overlapping shifts and exceeded weekly hours.
- **Scenario tools:** what-if simulation, emergency absence handling and automatic rebalancing after a leave is approved.
- **Bulk shift creation** and per-department shift recommendations.

### Workforce Management
- Employee and department CRUD with weekly hour and overtime limits.
- Leave requests with balance tracking, an approval workflow, auto-approval rules and analytics.
- Employee shift preferences (preferred days and shift types), collected from the mobile app.
- An audit trail for shift changes, plus soft delete.

### Real-Time & Notifications
- Server-Sent Events (`/events/stream`), with a polling fallback.
- An in-app notification center (info / warning / error / success).
- Push notifications on mobile through Firebase Cloud Messaging.

### Security AI Module
- A **hybrid detector** that combines a regex/AST rule engine with an ML model (TensorFlow). Results are fused using Conservative, Balanced or Aggressive strategies.
- Detects SQL injection, command injection, path traversal, hardcoded credentials and more.
- Scans single snippets, uploaded files, whole projects and API endpoints, then generates reports and quick-fix suggestions.
- Training toolkit: stratified and temporal data splitting, SMOTE and focal loss for class imbalance, evaluation benchmarks and continuous learning from feedback.
- A documented migration path to **MindSpore / Ascend NPU** (see [`backend/app/security_ai/migration`](backend/app/security_ai/migration/MIGRATION_PLAN.md)).

### Platform
- JWT authentication with role-based access control (**Admin / Manager / Employee**).
- Middleware for rate limiting, structured logging and security headers.
- Health, readiness and liveness probes, plus Prometheus-compatible `/metrics`.
- Background jobs with Celery + Redis for notifications, maintenance and scheduled optimization.
- Excel export from the web dashboard.

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
        D["Domain Services<br/>Rule Engine · Optimizer · Leave · Audit"]
        S["Security AI<br/>Hybrid Rule + ML Detector"]
        E["SSE Event Stream"]
    end

    subgraph Infra["Infrastructure"]
        DB[("PostgreSQL")]
        Q[("Redis")]
        C["Celery Workers"]
        F["Firebase Cloud Messaging"]
    end

    W -- "HTTPS / JSON" --> MW
    M -- "HTTPS / JSON" --> MW
    MW --> R --> D --> DB
    R --> S
    E -. "real-time" .-> W
    D --> Q --> C
    C --> F -. "push" .-> M
```

### Optimization flow

```mermaid
sequenceDiagram
    participant Mgr as Manager (Web)
    participant API as FastAPI
    participant Opt as ShiftOptimizationService
    participant RE as RuleEngine
    participant DB as PostgreSQL

    Mgr->>API: POST /api/v1/ai/optimize (period, department, strategy)
    API->>DB: Load employees, availability, preferences, rules
    API->>Opt: optimize_shifts(constraints)
    loop for each open shift
        Opt->>Opt: Score candidates (availability · workload · skills)
        Opt->>RE: Validate assignment (labor law, overtime, rest period)
        RE-->>Opt: Violations / OK
    end
    Opt-->>API: Assignments + score + warnings + explanation
    API-->>Mgr: Preview result
    Mgr->>API: POST /api/v1/ai/apply
    API->>DB: Persist shifts and write audit log
```

### Mobile offline-first sync

The mobile app keeps a local SQLite cache and a queue of pending operations. A `SyncService` pushes queued changes and pulls fresh data every 5 minutes, retrying up to 5 times when the device is online. When local and server data conflict, the server version wins.

---

## Tech Stack

| Layer | Technologies |
| --- | --- |
| **Backend** | Python, FastAPI, Uvicorn, SQLAlchemy 2, Alembic, Pydantic v2, psycopg 3 |
| **Auth & Security** | JWT (python-jose), bcrypt (passlib), RBAC, rate limiting middleware |
| **Async / Jobs** | Celery, Redis, Server-Sent Events |
| **Database** | PostgreSQL (GaussDB-compatible) |
| **ML** | TensorFlow, NumPy (MindSpore migration templates included) |
| **Web** | Next.js 16 (App Router), React 19, TypeScript, Ant Design 6, Tailwind CSS 4, Zustand, Axios, Recharts, Day.js, SheetJS |
| **Mobile** | Flutter / Dart, Provider, Dio, go_router, sqflite, flutter_secure_storage, connectivity_plus, Firebase Messaging, flutter_local_notifications |
| **Observability** | Health probes, Prometheus metrics endpoint, structured request logging |

---

## Repository Structure

```text
shift-planning-application/
├── backend/                      # FastAPI service
│   ├── alembic/                  # Database migrations
│   └── app/
│       ├── domain/               # Domain entities and services (rule engine, optimizer, leave, audit)
│       ├── middleware/           # Rate limiting, logging, security headers
│       ├── models/               # SQLAlchemy ORM models
│       ├── routers/              # REST endpoints (/api/v1)
│       ├── schemas/              # Pydantic request/response schemas
│       ├── security_ai/          # Hybrid vulnerability detection engine and ML toolkit
│       ├── tasks/                # Celery background jobs
│       └── utils/                # Security helpers (hashing, JWT)
├── web/ai-shiftmaster-web/       # Next.js admin and manager dashboard
│   └── app/
│       ├── dashboard/  employees/  shifts/  rules/  ai-optimization/
│       ├── security/             # Scan, rules, training, migration views
│       ├── landing/  login/  register/  profile/  settings/
│       ├── components/  lib/  store/  theme/  types/
│       └── data/                 # Sample employee preference dataset
├── employee_shift_mobile/        # Flutter employee app
│   └── lib/
│       ├── core/  data/  providers/  services/
│       └── presentation/         # Screens and widgets
├── docs/                         # Extended architecture notes
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
pip install -r requirements.txt

cp .env.example .env               # then set DATABASE_URL and SECRET_KEY
uvicorn app.main:app --reload
```

Tables are created automatically on first startup. The API runs at **http://localhost:8000**. Interactive docs are at `/docs` (Swagger) and `/redoc`.

<details>
<summary>Environment variables</summary>

| Variable | Description | Example |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@localhost:5432/shiftmaster` |
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

Open **http://localhost:3000**.

### 3. Mobile app

```bash
cd employee_shift_mobile
flutter pub get
flutter run
```

> When you run on an Android emulator, use `http://10.0.2.2:8000` to reach a backend running on the host machine.

### Development accounts

On first startup the backend seeds these accounts for local development. Change or remove them before you deploy.

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@example.com` | `admin123` |
| Manager | `manager@example.com` | `manager123` |
| Employee | `employee@example.com` | `employee123` |

---

## API Reference

All business endpoints are served under `/api/v1`. The full, always up-to-date contract is at `/docs` when the backend is running.

| Area | Endpoints |
| --- | --- |
| **Auth** | `POST /auth/login` · `POST /auth/register` · `POST /auth/refresh` · `POST /auth/logout` · `GET /auth/me` |
| **Employees** | `GET/POST /employees` · `GET/PUT/DELETE /employees/{id}` |
| **Departments** | `GET/POST /departments` · `GET/PUT/DELETE /departments/{id}` |
| **Shifts** | `GET/POST /shifts` · `GET/PUT/DELETE /shifts/{id}` · `GET /shifts/conflicts` · `POST /shifts/bulk` |
| **Shifts v2** | `GET /shifts/v2/validate/{employee_id}` · `POST /shifts/v2/optimized` · `GET /shifts/v2/recommendations/{department_id}` · `PUT /shifts/v2/{id}/soft-delete` · `GET /shifts/v2/audit/{id}` |
| **Shift rules** | `GET/POST /rules` · `GET/PUT/DELETE /rules/{id}` |
| **AI optimization** | `POST /ai/optimize` · `POST /ai/apply` |
| **Leave requests** | `GET/POST /leave-requests` · `GET /leave-requests/my` · `DELETE /leave-requests/{id}` |
| **Leave v2** | `GET /leave-requests/v2/balance/{employee_id}` · `POST /leave-requests/v2` · `PUT /leave-requests/v2/{id}/decide` · `GET /leave-requests/v2/pending` · `GET /leave-requests/v2/analytics` |
| **Notifications** | `GET /notifications` · `PUT /notifications/{id}/read` · `PUT /notifications/read-all` · `DELETE /notifications/{id}` |
| **Events** | `GET /events/stream` (SSE) · `GET /events/poll` · `GET /events/stats` |
| **Security AI** | `POST /security/scan/code` · `POST /security/scan/file` · `POST /security/scan/project` · `GET /security/scan/{id}` · `GET /security/scan/{id}/report` · `POST /security/api/scan` · `POST /security/quick-fix` · `GET /security/categories` |
| **Health** (root) | `GET /health` · `/health/ready` · `/health/live` · `/health/detailed` · `/metrics` · `/metrics/json` · `/info` |

---

## Data Model

```mermaid
erDiagram
    DEPARTMENT ||--o{ EMPLOYEE : employs
    DEPARTMENT ||--o{ SHIFT : schedules
    DEPARTMENT ||--o{ SHIFT_RULE : defines
    USER ||--o| EMPLOYEE : "is linked to"
    EMPLOYEE ||--o{ SHIFT : "is assigned"
    EMPLOYEE ||--o{ LEAVE_REQUEST : submits
    USER ||--o{ NOTIFICATION : receives
    USER ||--o{ AUDIT_LOG : performs
```

| Table | Description |
| --- | --- |
| `users` | Login accounts and roles |
| `departments` | Organizational units |
| `employees` | Employee profiles, availability, weekly hour and overtime limits |
| `shifts` | Scheduled shifts, including their source (manual or AI) |
| `shift_rules` | Staffing requirements per department, day and time range |
| `leave_requests` | Leave applications and approval state |
| `notifications` | User notifications |
| `audit_logs` | Change history for compliance |

---

## Security

- Passwords are hashed with **bcrypt**. Tokens are signed JWTs with a configurable lifetime.
- Role-based authorization is enforced on every protected endpoint and on Next.js routes through middleware.
- Request rate limiting and security headers are applied by middleware.
- Secrets are read from environment variables only. `.env` files are git-ignored, and `.env.example` documents the required keys.
- Pydantic validates the input of every endpoint.

---

## Roadmap

- [ ] Connect the web **Shift Rules**, **registration** and **Security AI dashboard** views to the live backend endpoints. They currently show sample data.
- [ ] Make the web **AI Optimization** page call the backend optimizer (`/ai/optimize`, `/shifts/v2/optimized`) instead of generating the schedule in the browser.
- [ ] Add a complete Alembic migration chain. Revision `002` is missing.
- [ ] Ship trained weights for the Security AI ML model. Until then, the detector runs in rule-based mode.
- [ ] Add an automated test suite (pytest, Playwright, Flutter widget tests) and a CI pipeline.
- [ ] Add Docker Compose for one-command local setup.
- [ ] Add configurable strategies for resolving offline sync conflicts on mobile.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
