"""End-to-end API tests against a temporary SQLite database."""

from datetime import date, timedelta

API = "/api/v1"


def next_monday() -> date:
    today = date.today()
    return today + timedelta(days=7 - today.weekday())


# --------------------------------------------------------------------------- auth

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_rejects_wrong_password(client):
    response = client.post(f"{API}/auth/login", json={"email": "admin@example.com", "password": "wrong"})
    assert response.status_code == 401


def test_me_returns_current_user(client, admin_headers):
    response = client.get(f"{API}/auth/me", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_protected_endpoint_requires_token(client):
    assert client.get(f"{API}/employees").status_code in (401, 403)


def test_register_cannot_choose_admin_role(client):
    response = client.post(
        f"{API}/auth/register",
        json={"email": "new.person@example.com", "name": "New Person", "password": "password123", "role": "admin"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["role"] == "employee"


def test_register_rejects_duplicate_email(client):
    response = client.post(
        f"{API}/auth/register",
        json={"email": "admin@example.com", "name": "Someone", "password": "password123"},
    )
    assert response.status_code == 400


def test_register_validates_password_length(client):
    response = client.post(
        f"{API}/auth/register",
        json={"email": "short@example.com", "name": "Short", "password": "123"},
    )
    assert response.status_code == 422


def test_employee_cannot_run_optimizer(client, employee_headers):
    response = client.post(
        f"{API}/ai/optimize",
        headers=employee_headers,
        json={"start_date": str(next_monday()), "end_date": str(next_monday())},
    )
    assert response.status_code == 403


# --------------------------------------------------------------------------- data setup

def _department(client, headers, name):
    existing = [d for d in client.get(f"{API}/departments", headers=headers).json() if d["name"] == name]
    if existing:
        return existing[0]["id"]
    response = client.post(f"{API}/departments", headers=headers, json={"name": name, "description": "Test"})
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def _employee(client, headers, dept_id, index, preferred="morning"):
    response = client.post(
        f"{API}/employees",
        headers=headers,
        json={
            "name": f"Test Person {index}",
            "email": f"test.person{index}@example.com",
            "password": "secret123",
            "role": "Operations Specialist",
            "department_id": dept_id,
            "weekly_working_limit": 40,
            "overtime_limit": 5,
            "preferences": {"preferred_shift": preferred, "weekly_off_day": 0},
        },
    )
    assert response.status_code in (200, 201), response.text
    return response.json()


# --------------------------------------------------------------------------- employees & preferences

def test_employee_crud_and_preferences(client, admin_headers, login):
    dept_id = _department(client, admin_headers, "Logistics")
    employee = _employee(client, admin_headers, dept_id, 100, preferred="night")
    assert employee["preferences"]["preferred_shift"] == "night"

    # The employee updates their own preferences (mobile app flow)
    headers = login("test.person100@example.com", "secret123")
    update = {"preferred_shift": "day", "weekly_off_day": 6, "work_model": "hybrid", "office_days": 3, "remote_days": 2}
    response = client.put(f"{API}/employees/me/preferences", headers=headers, json=update)
    assert response.status_code == 200, response.text
    assert client.get(f"{API}/employees/me/preferences", headers=headers).json()["preferred_shift"] == "day"

    # The manager sees the same values
    detail = client.get(f"{API}/employees/{employee['id']}", headers=admin_headers).json()
    assert detail["preferences"]["weekly_off_day"] == 6

    response = client.put(f"{API}/employees/{employee['id']}", headers=admin_headers, json={"weekly_working_limit": 32})
    assert response.status_code == 200
    assert response.json()["weekly_working_limit"] == 32


def test_invalid_preferences_are_rejected(client, login):
    headers = login("test.person100@example.com", "secret123")
    response = client.put(f"{API}/employees/me/preferences", headers=headers, json={"preferred_shift": "brunch"})
    assert response.status_code == 422


def test_preferences_require_employee_profile(client, admin_headers):
    assert client.get(f"{API}/employees/me/preferences", headers=admin_headers).status_code == 404


# --------------------------------------------------------------------------- shift rules

def test_shift_rule_crud(client, admin_headers):
    dept_id = _department(client, admin_headers, "Logistics")
    payload = {
        "name": "Weekday cover",
        "department_id": dept_id,
        "role": "Any",
        "start_time": "08:00",
        "end_time": "16:00",
        "min_employees": 2,
        "max_employees": 4,
        "days_of_week": [1, 2, 3, 4, 5],
        "is_active": True,
    }
    created = client.post(f"{API}/rules", headers=admin_headers, json=payload)
    assert created.status_code in (200, 201), created.text
    rule_id = created.json()["id"]

    updated = client.put(f"{API}/rules/{rule_id}", headers=admin_headers, json={"is_active": False})
    assert updated.status_code == 200
    assert updated.json()["is_active"] is False

    assert client.delete(f"{API}/rules/{rule_id}", headers=admin_headers).status_code in (200, 204)


# --------------------------------------------------------------------------- optimizer flow

def test_optimize_apply_and_rerun(client, admin_headers):
    dept_id = _department(client, admin_headers, "Warehouse")
    for i in range(12):
        _employee(client, admin_headers, dept_id, 200 + i, preferred=["morning", "day", "afternoon"][i % 3])

    monday = next_monday()
    request = {
        "start_date": str(monday),
        "end_date": str(monday + timedelta(days=4)),
        "department_ids": [dept_id],
        "settings": {"shift_types": ["morning", "day", "afternoon"], "min_employees_per_shift": 1},
    }

    preview = client.post(f"{API}/ai/optimize", headers=admin_headers, json=request)
    assert preview.status_code == 200, preview.text
    result = preview.json()
    assert result["shifts"], result["message"]
    assert result["metrics"]["coverage"] == 100.0
    assert not [c for c in result["conflicts"] if c["type"] == "understaffed"]
    assert all(s["id"] < 0 for s in result["shifts"])  # preview only, not saved yet

    applied = client.post(f"{API}/ai/apply", headers=admin_headers, json={"shifts": result["shifts"]})
    assert applied.status_code == 200, applied.text
    assert applied.json()["created_count"] == len(result["shifts"])

    # Running the same period again must not double-book anyone
    rerun = client.post(f"{API}/ai/optimize", headers=admin_headers, json=request).json()
    assert rerun["shifts"] == []
    assert rerun["metrics"]["coverage"] == 100.0

    summary = client.get(
        f"{API}/dashboard/summary",
        headers=admin_headers,
        params={"start_date": str(monday), "end_date": str(monday + timedelta(days=6))},
    )
    assert summary.status_code == 200
    assert summary.json()["total_shifts"] >= len(result["shifts"])
