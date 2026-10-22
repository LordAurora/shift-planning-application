from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from app.database import get_db
from app.models.shift import Shift
from app.models.employee import Employee
from app.models.user import User
from app.domain.services.schedule_optimizer import (
    EmployeeInput,
    ExistingShift,
    OptimizerSettings,
    ScheduleOptimizer,
)
from app.schemas.ai import (
    ApplyOptimizationRequest,
    OptimizationMetrics,
    OptimizationRequest,
    OptimizationResult,
    OptimizedShift,
)
from app.schemas.shift import ShiftConflict, ShiftStatus
from app.utils.security import require_role

router = APIRouter(prefix="/ai", tags=["AI Optimization"])

DAY_NAMES = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]


def _to_local_naive(value: datetime) -> datetime:
    """Schedules are planned in local wall-clock time."""
    return value.astimezone().replace(tzinfo=None) if value.tzinfo else value


def _employee_input(emp: Employee) -> EmployeeInput:
    prefs = emp.preferences or {}
    off_day = prefs.get("weekly_off_day")
    if isinstance(off_day, str):
        off_day = DAY_NAMES.index(off_day.lower()) if off_day.lower() in DAY_NAMES else None
    available = {slot.get("day") for slot in (emp.availability or []) if isinstance(slot, dict)}
    return EmployeeInput(
        id=emp.id,
        name=emp.name,
        department_id=emp.department_id,
        department_name=emp.department.name if emp.department else None,
        weekly_limit=emp.weekly_working_limit or 40.0,
        overtime_limit=emp.overtime_limit or 0.0,
        available_days=available or None,
        preferred_shift=prefs.get("preferred_shift"),
        weekly_off_day=off_day,
    )


@router.post("/optimize", response_model=OptimizationResult)
async def optimize_shifts(
    request: OptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """
    Generate an optimized shift schedule (preview only, nothing is saved).

    The optimizer respects weekly hour caps, rest periods, consecutive-day limits,
    availability and days off, then ranks candidates by shift preference and
    workload balance. Existing shifts in the period are taken into account.
    """
    query = db.query(Employee).options(joinedload(Employee.department))
    if request.department_ids:
        query = query.filter(Employee.department_id.in_(request.department_ids))
    employees = query.all()

    if not employees:
        return OptimizationResult(
            shifts=[], conflicts=[], optimization_score=0.0,
            message="No employees found for the selected departments.",
        )

    # Existing shifts (including the week before) count towards hours and rest periods
    window_start = datetime.combine(request.start_date - timedelta(days=7), datetime.min.time())
    window_end = datetime.combine(request.end_date + timedelta(days=1), datetime.min.time())
    existing_rows = (
        db.query(Shift)
        .filter(
            Shift.employee_id.in_([e.id for e in employees]),
            Shift.status != ShiftStatus.CANCELLED,
            Shift.start_time >= window_start,
            Shift.start_time < window_end,
        )
        .all()
    )
    existing = [
        ExistingShift(s.employee_id, _to_local_naive(s.start_time), _to_local_naive(s.end_time), s.department_id)
        for s in existing_rows
    ]

    settings = OptimizerSettings(**request.settings.model_dump())
    outcome = ScheduleOptimizer(settings).optimize(
        [_employee_input(e) for e in employees],
        request.start_date,
        request.end_date,
        existing,
    )

    now = datetime.now()
    shifts = [
        OptimizedShift(
            id=-(index + 1),  # temporary ids until the schedule is applied
            employee_id=a.employee_id,
            employee_name=a.employee_name,
            department_id=a.department_id,
            department_name=a.department_name,
            start_time=a.start,
            end_time=a.end,
            status=ShiftStatus.SCHEDULED,
            shift_type=a.shift_type,
            preferred=a.preferred,
            created_at=now,
            updated_at=now,
        )
        for index, a in enumerate(outcome.assignments)
    ]
    conflicts = [
        ShiftConflict(type=w.type, message=w.message, employee_id=w.employee_id, shift_ids=[])
        for w in outcome.warnings
    ]
    metrics = {k: v for k, v in outcome.metrics.items() if k != "score"}

    return OptimizationResult(
        shifts=shifts,
        conflicts=conflicts,
        optimization_score=outcome.score,
        metrics=OptimizationMetrics(**metrics),
        message=(
            f"Generated {len(shifts)} shifts for {metrics['employees_scheduled']} employees "
            f"with {len(conflicts)} warning(s)."
        ),
    )


@router.post("/apply")
async def apply_optimization(
    request: ApplyOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """
    Apply optimized shifts to the database.
    
    This endpoint takes the generated shifts from the optimization
    and creates them in the database.
    """
    created = [
        Shift(
            employee_id=shift_data.employee_id,
            department_id=shift_data.department_id,
            # Naive timestamps come from the optimizer preview and are local wall-clock time
            start_time=shift_data.start_time if shift_data.start_time.tzinfo else shift_data.start_time.astimezone(),
            end_time=shift_data.end_time if shift_data.end_time.tzinfo else shift_data.end_time.astimezone(),
            status=shift_data.status,
        )
        for shift_data in request.shifts
    ]
    db.add_all(created)
    db.commit()

    return {
        "message": f"Successfully created {len(created)} shifts",
        "created_count": len(created),
    }
