from datetime import date, datetime, timedelta

from app.domain.services.schedule_optimizer import (
    EmployeeInput,
    ExistingShift,
    OptimizerSettings,
    ScheduleOptimizer,
)

MONDAY = date(2026, 11, 16)


def team(n=12, dept=1, **overrides):
    return [
        EmployeeInput(id=i + 1, name=f"Employee {i + 1}", department_id=dept, department_name="Engineering", **overrides)
        for i in range(n)
    ]


def run(employees, start=MONDAY, days=7, existing=(), **settings):
    optimizer = ScheduleOptimizer(OptimizerSettings(**settings))
    return optimizer.optimize(employees, start, start + timedelta(days=days - 1), existing)


def hours_per_employee_week(assignments):
    totals = {}
    for a in assignments:
        totals[a.employee_id] = totals.get(a.employee_id, 0) + (a.end - a.start).total_seconds() / 3600
    return totals


def test_one_shift_per_employee_per_day():
    result = run(team())
    seen = set()
    for a in result.assignments:
        key = (a.employee_id, a.start.date())
        assert key not in seen
        seen.add(key)


def test_weekly_hour_cap_is_respected():
    result = run(team(), max_hours_per_week=24)
    assert max(hours_per_employee_week(result.assignments).values()) <= 24


def test_only_operating_days_are_scheduled():
    result = run(team(), operating_days=["monday", "wednesday"])
    assert {a.start.weekday() for a in result.assignments} == {0, 2}


def test_weekly_off_day_is_honoured():
    employees = team(weekly_off_day=1)  # Monday (Sunday-based numbering)
    result = run(employees)
    assert all(a.start.weekday() != 0 for a in result.assignments)


def test_minimum_rest_between_shifts():
    employees = team(4)
    result = run(employees, shift_types=["morning", "afternoon", "night"], min_rest_hours=11, is_24_7=True)
    by_emp = {}
    for a in sorted(result.assignments, key=lambda a: a.start):
        prev = by_emp.get(a.employee_id)
        if prev:
            assert (a.start - prev.end).total_seconds() / 3600 >= 11
        by_emp[a.employee_id] = a


def test_existing_shifts_count_towards_weekly_hours():
    employees = team(1)
    existing = [ExistingShift(1, datetime(2026, 11, 16, 9), datetime(2026, 11, 16, 17))]
    result = run(employees, existing=existing, max_hours_per_week=16, min_employees_per_shift=0)
    assert sum(hours_per_employee_week(result.assignments).values()) <= 8
    assert all(a.start.date() != MONDAY for a in result.assignments)


def test_preferences_raise_preference_match():
    employees = [
        EmployeeInput(id=i + 1, name=f"E{i}", department_id=1, department_name="Ops",
                      preferred_shift=["morning", "day", "afternoon"][i % 3])
        for i in range(15)
    ]
    with_prefs = run(employees, consider_preferences=True, preference_weight=90)
    without = run(employees, consider_preferences=False)
    match = lambda r: sum(a.preferred for a in r.assignments) / len(r.assignments)
    assert match(with_prefs) > match(without)
    assert with_prefs.metrics["preference_match"] >= 80


def test_understaffed_slots_produce_warnings():
    result = run(team(1), min_employees_per_shift=3, days=1)
    assert any(w.type == "understaffed" for w in result.warnings)


def test_result_is_deterministic():
    a = run(team(20))
    b = run(team(20))
    assert [(x.employee_id, x.start) for x in a.assignments] == [(x.employee_id, x.start) for x in b.assignments]
    assert 0 <= a.score <= 100


def test_existing_shifts_fill_slots_without_false_warnings():
    employees = team(12)
    first = run(employees, days=1)
    existing = [ExistingShift(a.employee_id, a.start, a.end, a.department_id) for a in first.assignments]
    second = run(employees, days=1, existing=existing)
    assert second.assignments == []
    assert not any(w.type == "understaffed" for w in second.warnings)
    assert second.metrics["coverage"] == 100.0
