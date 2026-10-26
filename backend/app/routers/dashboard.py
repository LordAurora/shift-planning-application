"""Aggregated metrics for the web dashboard, computed from real shift data."""

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.department import Department
from app.models.employee import Employee
from app.models.shift import Shift, ShiftStatus
from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _local(value: datetime) -> datetime:
    return value.astimezone().replace(tzinfo=None) if value.tzinfo else value


def _shift_type(start: datetime) -> str:
    hour = start.hour
    if 4 <= hour < 8:
        return "Morning"
    if 8 <= hour < 12:
        return "Day"
    if 12 <= hour < 20:
        return "Evening"
    return "Night"


@router.get("/summary")
def dashboard_summary(
    start_date: Optional[date] = Query(None, description="Defaults to the start of the current week"),
    end_date: Optional[date] = Query(None, description="Defaults to the end of the current week"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    start_date = start_date or today - timedelta(days=today.weekday())
    end_date = end_date or start_date + timedelta(days=6)
    period_start = datetime.combine(start_date, datetime.min.time()).astimezone()
    period_end = datetime.combine(end_date + timedelta(days=1), datetime.min.time()).astimezone()

    shifts = (
        db.query(Shift)
        .options(joinedload(Shift.employee), joinedload(Shift.department))
        .filter(Shift.start_time >= period_start, Shift.start_time < period_end)
        .order_by(Shift.start_time)
        .all()
    )
    active = [s for s in shifts if s.status != ShiftStatus.CANCELLED]

    total_employees = db.query(func.count(Employee.id)).scalar() or 0
    departments = (
        db.query(Department.name, func.count(Employee.id))
        .outerjoin(Employee, Employee.department_id == Department.id)
        .group_by(Department.name)
        .order_by(Department.name)
        .all()
    )

    hours_by_employee = defaultdict(float)
    by_weekday = {d: {"name": d, "shifts": 0, "hours": 0.0, "employees": set()} for d in WEEKDAYS}
    types = Counter()
    for s in active:
        start, end = _local(s.start_time), _local(s.end_time)
        hours = (end - start).total_seconds() / 3600
        hours_by_employee[s.employee_id] += hours
        bucket = by_weekday[WEEKDAYS[start.weekday()]]
        bucket["shifts"] += 1
        bucket["hours"] += hours
        bucket["employees"].add(s.employee_id)
        types[_shift_type(start)] += 1

    weeks = max(((end_date - start_date).days + 1) / 7, 1)
    overtime = 0
    if hours_by_employee:
        limits = dict(db.query(Employee.id, Employee.weekly_working_limit).filter(Employee.id.in_(hours_by_employee)).all())
        overtime = sum(1 for emp, h in hours_by_employee.items() if h / weeks > (limits.get(emp) or 40))

    # Six-month trend, independent of the selected period
    trend_start = (today.replace(day=1) - timedelta(days=150)).replace(day=1)
    trend_rows = (
        db.query(Shift.start_time, Shift.status)
        .filter(Shift.start_time >= datetime.combine(trend_start, datetime.min.time()).astimezone())
        .all()
    )
    trend = defaultdict(Counter)
    for start, status in trend_rows:
        trend[_local(start).strftime("%Y-%m")][status.value] += 1
    months = []
    cursor = trend_start
    for _ in range(6):
        key = cursor.strftime("%Y-%m")
        months.append({
            "month": cursor.strftime("%b"),
            "scheduled": trend[key]["scheduled"],
            "completed": trend[key]["completed"],
            "cancelled": trend[key]["cancelled"],
        })
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    upcoming = [
        {
            "id": s.id,
            "employee": s.employee.name if s.employee else None,
            "department": s.department.name if s.department else None,
            "start_time": _local(s.start_time).isoformat(),
            "end_time": _local(s.end_time).isoformat(),
            "status": s.status.value,
        }
        for s in active
        if _local(s.start_time) >= datetime.now()
    ][:8]

    return {
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "total_employees": total_employees,
        "total_departments": len(departments),
        "total_shifts": len(active),
        "total_hours": round(sum(hours_by_employee.values()), 1),
        "employees_scheduled": len(hours_by_employee),
        "over_contract": overtime,
        "cancelled_shifts": len(shifts) - len(active),
        "by_weekday": [
            {**v, "hours": round(v["hours"], 1), "employees": len(v["employees"])} for v in by_weekday.values()
        ],
        "shift_types": [{"name": k, "value": types.get(k, 0)} for k in ("Morning", "Day", "Evening", "Night")],
        "departments": [{"name": name, "value": count} for name, count in departments],
        "monthly_trend": months,
        "upcoming_shifts": upcoming,
    }
