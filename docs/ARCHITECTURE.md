# Architecture Notes

These notes go one level deeper than the [README](../README.md): how the parts of the monorepo fit together and where to find things.

## 1. Overview

| Component | Path | Role |
| --- | --- | --- |
| Backend | [`backend/`](../backend) | FastAPI REST API, scheduling engine, persistence, background jobs |
| Web dashboard | [`web/ai-shiftmaster-web/`](../web/ai-shiftmaster-web) | Next.js app for admins and managers, plus the public landing page |
| Mobile app | [`employee_shift_mobile/`](../employee_shift_mobile) | Flutter app for employees, offline-first |

Both clients talk to the same REST API (`/api/v1`) over JSON with JWT bearer tokens.

## 2. Backend

- **Entry point:** [`app/main.py`](../backend/app/main.py) sets up middleware, registers the routers and seeds the development accounts.
- **Configuration:** [`app/config.py`](../backend/app/config.py) reads environment variables. [`app/database.py`](../backend/app/database.py) creates the SQLAlchemy engine and always uses the psycopg 3 driver.
- **Layers:**
  - `models/`: SQLAlchemy ORM models
  - `schemas/`: Pydantic request and response models
  - `routers/`: HTTP endpoints, kept thin
  - `domain/services/`: business logic: the [schedule optimizer](../backend/app/domain/services/schedule_optimizer.py), the labor rule engine, leave and audit services
  - `middleware/`: rate limiting, structured request logging, security headers
  - `tasks/`: Celery jobs for notifications, maintenance and scheduled work
- **Migrations:** [`alembic/versions/`](../backend/alembic/versions)

| Revision | Change |
| --- | --- |
| `001_initial_schema` | Users, departments, employees, shifts, rules, notifications, audit logs |
| `002_add_leave_requests` | Leave requests |
| `003_performance_indexes` | Indexes for calendar, per-employee and audit queries |
| `004_employee_preferences` | `employees.preferences` (preferred shift, day off, work model) |

## 3. Scheduling engine

`ScheduleOptimizer` works through the schedule in this order: each day, then each shift type, then each department. For each slot it:

1. Computes the demand from team size and contract hours, clamped to the configured minimum and maximum staffing.
2. Subtracts the people already staffed by existing shifts.
3. Filters out candidates who would break a hard constraint: a second shift that day, the weekly hour cap, the minimum rest period, the consecutive-day limit, unavailability or their weekly day off.
4. Ranks the remaining candidates by `w × preference + (1 − w) × workload balance`, with a deterministic tie-breaker.
5. Assigns the top candidates, and records overtime and understaffing warnings.

Every result includes coverage, preference match, fairness and a combined score. `POST /ai/optimize` only returns a preview; `POST /ai/apply` saves it. Timestamps in the preview are local wall-clock times, and the apply endpoint converts them to timezone-aware values.

The engine has no framework dependencies and is covered by [`tests/test_schedule_optimizer.py`](../backend/tests/test_schedule_optimizer.py).

## 4. Web dashboard

- Next.js App Router, React 19, Ant Design 6 and Zustand.
- [`app/lib/api.ts`](../web/ai-shiftmaster-web/app/lib/api.ts) is an Axios client that attaches the token and handles `401` responses. [`app/lib/services.ts`](../web/ai-shiftmaster-web/app/lib/services.ts) holds the typed API calls.
- [`middleware.ts`](../web/ai-shiftmaster-web/middleware.ts) protects routes by role, using cookies mirrored from the auth store.
- Public pages are `/landing`, `/login` and `/register`. Everything else sits inside `DashboardLayout`.

## 5. Mobile app

- Uses Provider for state, Dio for HTTP, `flutter_secure_storage` for tokens and `sqflite` for the offline cache.
- **SyncService:** connectivity-aware sync that runs every 5 minutes with up to 5 retries. When local and server data conflict, the server version wins. While offline, changes are queued.
- **Preferences:** saved with `GET/PUT /employees/me/preferences`, which reads and writes the same field the optimizer uses.

## 6. Security model

- JWT access tokens and bcrypt password hashes.
- Roles: `admin`, `manager`, `employee`. Self-service sign-up cannot choose a role; the first account becomes the administrator.
- Secrets live only in environment variables, and `.env` files are git-ignored.
