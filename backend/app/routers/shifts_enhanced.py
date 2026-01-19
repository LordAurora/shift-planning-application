"""
Enhanced shifts router with domain service integration.

This router extends the base shifts functionality with:
- Rule engine validation
- Audit logging
- Permission-based access control
- Real-time event broadcasting
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from math import ceil

from app.database import get_db
from app.models.shift import Shift
from app.models.employee import Employee
from app.models.department import Department
from app.models.user import User
from app.schemas.shift import (
    ShiftCreate,
    ShiftUpdate,
    ShiftResponse,
    ShiftListResponse,
    ShiftConflict
)
from app.utils.security import get_current_user, require_role
from app.domain.container import (
    get_rule_engine,
    get_audit_service,
    get_shift_service,
    get_permission_service
)
from app.domain.services.rule_engine import RuleEngine
from app.domain.services.audit_service import AuditService
from app.domain.services.shift_optimization_service import ShiftOptimizationService
from app.domain.services.permission_service import (
    PermissionService,
    Permission,
    UserContext,
    ResourceContext
)
from app.domain.models.shift import ShiftEntity, ShiftStatus
from app.domain.models.employee import EmployeeEntity

# Try importing events for real-time notifications
try:
    from app.routers.events import notify_shift_change
    HAS_EVENTS = True
except ImportError:
    HAS_EVENTS = False


router = APIRouter(prefix="/shifts/v2", tags=["Shifts V2 (Enhanced)"])


def convert_to_domain_shift(shift: Shift) -> ShiftEntity:
    """Convert SQLAlchemy Shift model to domain ShiftEntity."""
    return ShiftEntity(
        id=shift.id,
        employee_id=shift.employee_id,
        department_id=shift.department_id,
        start_time=shift.start_time,
        end_time=shift.end_time,
        status=ShiftStatus(shift.status) if shift.status else ShiftStatus.SCHEDULED,
        created_at=shift.created_at,
        updated_at=shift.updated_at
    )


def convert_to_domain_employee(emp: Employee) -> EmployeeEntity:
    """Convert SQLAlchemy Employee model to domain EmployeeEntity."""
    return EmployeeEntity(
        id=emp.id,
        name=emp.name,
        email=emp.email,
        department_id=emp.department_id,
        max_hours_per_week=emp.weekly_working_limit,
        max_overtime_hours=emp.overtime_limit,
        min_hours_per_week=20,  # Default, could be from employee model
        skills=set(),  # Could be from a skills relationship
        is_active=emp.is_active
    )


def get_user_context(current_user: User) -> UserContext:
    """Convert current user to UserContext for permission checking."""
    from app.domain.services.permission_service import Role
    role_map = {
        'admin': Role.ADMIN,
        'manager': Role.MANAGER,
        'employee': Role.EMPLOYEE
    }
    return UserContext(
        user_id=current_user.id,
        role=role_map.get(current_user.role, Role.EMPLOYEE),
        department_id=getattr(current_user, 'department_id', None)
    )


@router.get("/validate/{employee_id}")
async def validate_shift_assignment(
    employee_id: int,
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rule_engine: RuleEngine = Depends(get_rule_engine)
):
    """
    Validate a potential shift assignment against business rules.
    
    Returns all rule violations without creating the shift.
    Useful for pre-validation before assignment.
    """
    # Get employee data
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Create domain entities
    domain_employee = convert_to_domain_employee(employee)
    proposed_shift = ShiftEntity(
        id=0,  # New shift
        employee_id=employee_id,
        department_id=employee.department_id,
        start_time=start_time,
        end_time=end_time,
        status=ShiftStatus.SCHEDULED
    )
    
    # Get existing shifts for the employee (this week)
    week_start = start_time - timedelta(days=start_time.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    
    existing_shifts_db = db.query(Shift).filter(
        Shift.employee_id == employee_id,
        Shift.status != "cancelled",
        Shift.start_time >= week_start,
        Shift.start_time < week_end
    ).all()
    
    existing_shifts = [convert_to_domain_shift(s) for s in existing_shifts_db]
    
    # Validate using rule engine
    violations = rule_engine.validate_shift(proposed_shift, domain_employee, existing_shifts)
    
    return {
        "is_valid": len(violations) == 0,
        "violations": [
            {
                "rule": v.rule_name,
                "message": v.message,
                "severity": v.severity,
                "details": v.details
            }
            for v in violations
        ],
        "employee": {
            "id": employee.id,
            "name": employee.name,
            "current_weekly_hours": domain_employee.calculate_current_workload(existing_shifts),
            "max_weekly_hours": employee.weekly_working_limit + employee.overtime_limit
        }
    }


@router.post("/optimized", response_model=ShiftResponse)
async def create_optimized_shift(
    shift_data: ShiftCreate,
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="Create shift even with rule violations"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
    rule_engine: RuleEngine = Depends(get_rule_engine),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Create a new shift with rule validation and audit logging.
    
    - Validates against all business rules (labor law, overtime, rest periods)
    - Logs creation in audit trail
    - Broadcasts real-time update to connected clients
    - Use force=true to override warnings (not errors)
    """
    # Validate employee exists
    employee = db.query(Employee).filter(Employee.id == shift_data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee not found"
        )
    
    # Validate department exists
    department = db.query(Department).filter(Department.id == shift_data.department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department not found"
        )
    
    # Create domain entities for validation
    domain_employee = convert_to_domain_employee(employee)
    proposed_shift = ShiftEntity(
        id=0,
        employee_id=shift_data.employee_id,
        department_id=shift_data.department_id,
        start_time=shift_data.start_time,
        end_time=shift_data.end_time,
        status=ShiftStatus.SCHEDULED
    )
    
    # Get existing shifts for validation
    week_start = shift_data.start_time - timedelta(days=shift_data.start_time.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    
    existing_shifts_db = db.query(Shift).filter(
        Shift.employee_id == shift_data.employee_id,
        Shift.status != "cancelled",
        Shift.start_time >= week_start,
        Shift.start_time < week_end
    ).all()
    existing_shifts = [convert_to_domain_shift(s) for s in existing_shifts_db]
    
    # Validate using rule engine
    violations = rule_engine.validate_shift(proposed_shift, domain_employee, existing_shifts)
    
    # Check for errors (non-overridable violations)
    errors = [v for v in violations if v.severity == 'error']
    warnings = [v for v in violations if v.severity == 'warning']
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Shift violates business rules",
                "violations": [
                    {"rule": v.rule_name, "message": v.message, "severity": v.severity}
                    for v in errors
                ]
            }
        )
    
    if warnings and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Shift has warnings. Use force=true to override.",
                "violations": [
                    {"rule": v.rule_name, "message": v.message, "severity": v.severity}
                    for v in warnings
                ]
            }
        )
    
    # Create shift
    shift = Shift(
        employee_id=shift_data.employee_id,
        department_id=shift_data.department_id,
        start_time=shift_data.start_time,
        end_time=shift_data.end_time,
        status=shift_data.status
    )
    
    db.add(shift)
    db.commit()
    db.refresh(shift)
    
    # Log to audit trail
    audit_entry = audit_service.log_shift_assignment(
        shift_id=shift.id,
        employee_id=shift.employee_id,
        user_id=current_user.id,
        department_id=shift.department_id,
        action_type="create",
        details={
            "start_time": shift.start_time.isoformat(),
            "end_time": shift.end_time.isoformat(),
            "warnings_overridden": len(warnings) if force else 0
        }
    )
    
    # Broadcast real-time update
    if HAS_EVENTS:
        background_tasks.add_task(
            notify_shift_change,
            shift_id=shift.id,
            action="created",
            department_id=shift.department_id
        )
    
    return ShiftResponse(
        id=shift.id,
        employee_id=shift.employee_id,
        employee_name=employee.name,
        department_id=shift.department_id,
        department_name=department.name,
        start_time=shift.start_time,
        end_time=shift.end_time,
        status=shift.status,
        created_at=shift.created_at,
        updated_at=shift.updated_at
    )


@router.get("/recommendations/{department_id}")
async def get_shift_recommendations(
    department_id: int,
    date: date,
    shift_count: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
    shift_service: ShiftOptimizationService = Depends(get_shift_service)
):
    """
    Get AI-powered shift assignment recommendations for a department.
    
    Returns ranked employee recommendations based on:
    - Current workload balance
    - Skills and preferences
    - Rest period requirements
    - Historical performance
    """
    # Get department employees
    employees_db = db.query(Employee).filter(
        Employee.department_id == department_id,
        Employee.is_active == True
    ).all()
    
    if not employees_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active employees in department"
        )
    
    # Get current shifts for the week
    week_start = datetime.combine(date - timedelta(days=date.weekday()), datetime.min.time())
    week_end = week_start + timedelta(days=7)
    
    current_shifts_db = db.query(Shift).filter(
        Shift.department_id == department_id,
        Shift.status != "cancelled",
        Shift.start_time >= week_start,
        Shift.start_time < week_end
    ).all()
    
    # Convert to domain entities
    employees = [convert_to_domain_employee(e) for e in employees_db]
    current_shifts = [convert_to_domain_shift(s) for s in current_shifts_db]
    
    # Create a sample shift slot for recommendation
    shift_date = datetime.combine(date, datetime.min.time())
    proposed_shift = ShiftEntity(
        id=0,
        employee_id=0,  # To be assigned
        department_id=department_id,
        start_time=shift_date.replace(hour=9),
        end_time=shift_date.replace(hour=17),
        status=ShiftStatus.SCHEDULED
    )
    
    # Get recommendations using optimization service
    recommendations = shift_service.get_optimal_assignment(
        employees=employees,
        shift=proposed_shift,
        current_schedule=current_shifts
    )
    
    # Return top N recommendations
    result = []
    for i, rec in enumerate(recommendations[:shift_count]):
        emp = next((e for e in employees_db if e.id == rec.employee_id), None)
        if emp:
            result.append({
                "rank": i + 1,
                "employee_id": rec.employee_id,
                "employee_name": emp.name,
                "score": rec.score,
                "reasoning": rec.reasoning,
                "warnings": rec.warnings
            })
    
    return {
        "date": date.isoformat(),
        "department_id": department_id,
        "recommendations": result
    }


@router.put("/{shift_id}/soft-delete")
async def soft_delete_shift(
    shift_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"])),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Soft-delete a shift (preserves data for audit trail).
    
    Sets is_deleted=true instead of removing the record.
    """
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )
    
    # Check if already deleted
    if getattr(shift, 'is_deleted', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shift already deleted"
        )
    
    # Store before state for audit
    before_state = {
        "id": shift.id,
        "employee_id": shift.employee_id,
        "status": shift.status,
        "is_deleted": False
    }
    
    # Soft delete
    if hasattr(shift, 'is_deleted'):
        shift.is_deleted = True
        shift.deleted_at = datetime.utcnow()
        shift.deleted_by = current_user.id
    else:
        # Fallback: change status to cancelled if soft-delete not available
        shift.status = "cancelled"
    
    db.commit()
    
    # Log to audit trail
    audit_service.log_shift_assignment(
        shift_id=shift.id,
        employee_id=shift.employee_id,
        user_id=current_user.id,
        department_id=shift.department_id,
        action_type="delete",
        before_state=before_state,
        details={"soft_delete": True}
    )
    
    # Broadcast real-time update
    if HAS_EVENTS:
        background_tasks.add_task(
            notify_shift_change,
            shift_id=shift.id,
            action="deleted",
            department_id=shift.department_id
        )
    
    return {"message": "Shift soft-deleted successfully", "shift_id": shift_id}


@router.get("/audit/{shift_id}")
async def get_shift_audit_trail(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """
    Get complete audit trail for a shift.
    
    Returns all changes made to the shift, including:
    - Who made each change
    - When changes were made
    - Before/after states
    """
    # Query audit logs for this shift
    # This would query the audit_logs table
    # For now, return a placeholder
    return {
        "shift_id": shift_id,
        "audit_entries": [],
        "message": "Audit trail requires audit_logs table query"
    }
