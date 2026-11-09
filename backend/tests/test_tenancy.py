"""Every company only sees its own data."""

from datetime import date, timedelta

API = "/api/v1"


def _new_company(client, login, slug):
    response = client.post(
        f"{API}/auth/register",
        json={
            "company_name": f"{slug.title()} Corp",
            "email": f"admin@{slug}.example.com",
            "name": f"{slug.title()} Admin",
            "password": "password123",
        },
    )
    assert response.status_code == 201, response.text
    return login(f"admin@{slug}.example.com", "password123")


def _setup(client, headers, slug, people=4):
    dept = client.post(f"{API}/departments", headers=headers, json={"name": "Engineering", "description": slug})
    assert dept.status_code in (200, 201), dept.text
    dept_id = dept.json()["id"]
    employees = []
    for i in range(people):
        response = client.post(
            f"{API}/employees",
            headers=headers,
            json={
                "name": f"{slug} person {i}",
                "email": f"p{i}@{slug}.example.com",
                "password": "secret123",
                "role": "Engineer",
                "department_id": dept_id,
            },
        )
        assert response.status_code in (200, 201), response.text
        employees.append(response.json())
    return dept_id, employees


def test_new_workspace_starts_empty(client, login):
    headers = _new_company(client, login, "empty")
    assert client.get(f"{API}/employees", headers=headers).json()["total"] == 0
    assert client.get(f"{API}/departments", headers=headers).json() == []
    assert client.get(f"{API}/rules", headers=headers).json() == []


def test_companies_are_isolated(client, login):
    alpha = _new_company(client, login, "alpha")
    beta = _new_company(client, login, "beta")

    # Both companies may use the same department name
    alpha_dept, alpha_people = _setup(client, alpha, "alpha")
    beta_dept, beta_people = _setup(client, beta, "beta", people=2)

    alpha_list = client.get(f"{API}/employees", headers=alpha).json()
    assert alpha_list["total"] == 4
    assert all(e["email"].endswith("@alpha.example.com") for e in alpha_list["items"])
    assert client.get(f"{API}/employees", headers=beta).json()["total"] == 2

    # Direct access to another company's records looks like "not found"
    foreign = alpha_people[0]["id"]
    assert client.get(f"{API}/employees/{foreign}", headers=beta).status_code == 404
    assert client.put(f"{API}/employees/{foreign}", headers=beta, json={"name": "Hijacked"}).status_code == 404
    assert client.delete(f"{API}/employees/{foreign}", headers=beta).status_code == 404
    assert client.get(f"{API}/employees/{foreign}", headers=alpha).json()["name"] == "alpha person 0"

    # Referencing another company's department is rejected
    response = client.post(
        f"{API}/employees",
        headers=beta,
        json={
            "name": "Sneaky",
            "email": "sneaky@beta.example.com",
            "password": "secret123",
            "role": "Engineer",
            "department_id": alpha_dept,
        },
    )
    assert response.status_code in (400, 404)

    # The optimizer only schedules the caller's own employees
    monday = date.today() + timedelta(days=7 - date.today().weekday())
    result = client.post(
        f"{API}/ai/optimize",
        headers=beta,
        json={"start_date": str(monday), "end_date": str(monday + timedelta(days=2)), "settings": {"min_employees_per_shift": 1}},
    ).json()
    beta_ids = {p["id"] for p in beta_people}
    assert result["shifts"]
    assert {s["employee_id"] for s in result["shifts"]} <= beta_ids

    # Dashboards count only the caller's data
    summary = client.get(f"{API}/dashboard/summary", headers=beta).json()
    assert summary["total_employees"] == 2
    assert summary["total_departments"] == 1


def test_emails_stay_globally_unique_across_companies(client, login):
    gamma = _new_company(client, login, "gamma")
    _setup(client, gamma, "gamma", people=0)
    dept_id = client.get(f"{API}/departments", headers=gamma).json()[0]["id"]
    response = client.post(
        f"{API}/employees",
        headers=gamma,
        json={
            "name": "Copycat",
            "email": "admin@example.com",  # belongs to the demo workspace
            "password": "secret123",
            "role": "Engineer",
            "department_id": dept_id,
        },
    )
    assert response.status_code == 400
