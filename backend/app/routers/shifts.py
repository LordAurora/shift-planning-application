from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
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
    ShiftConflict,
    ShiftBulkCreate,
    ShiftBulkResponse
)
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/shifts", tags=["Shifts"])


def check_shift_conflicts(
    db: Session,
    employee_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_shift_id: Optional[int] = None
) -> List[ShiftConflict]:
    """Check for shift conflicts"""
    conflicts = []
    
    # Check for overlapping shifts
    overlap_query = db.query(Shift).filter(
        Shift.employee_id == employee_id,
        Shift.status != "cancelled",
        Shift.start_time < end_time,
        Shift.end_time > start_time
    )
    
    if exclude_shift_id:
        overlap_query = overlap_query.filter(Shift.id != exclude_shift_id)
    
    overlapping_shifts = overlap_query.all()
    
    if overlapping_shifts:
        conflicts.append(ShiftConflict(
            type="overlap",
            message=f"Shift overlaps with {len(overlapping_shifts)} existing shift(s)",
            employee_id=employee_id,
            shift_ids=[s.id for s in overlapping_shifts]
        ))
    
    # Check weekly overtime
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if employee:
        # Get week boundaries
        week_start = start_time - timedelta(days=start_time.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        
        # Calculate total hours for the week
        week_shifts = db.query(Shift).filter(
            Shift.employee_id == employee_id,
            Shift.status != "cancelled",
            Shift.start_time >= week_start,
            Shift.start_time < week_end
        )
        
        if exclude_shift_id:
            week_shifts = week_shifts.filter(Shift.id != exclude_shift_id)
        
        week_shifts = week_shifts.all()
        
        total_hours = sum(
            (s.end_time - s.start_time).total_seconds() / 3600 
            for s in week_shifts
        )
        new_shift_hours = (end_time - start_time).total_seconds() / 3600
        total_with_new = total_hours + new_shift_hours
        
        max_hours = employee.weekly_working_limit + employee.overtime_limit
        
        if total_with_new > max_hours:
            conflicts.append(ShiftConflict(
                type="overtime",
                message=f"Total weekly hours ({total_with_new:.1f}h) exceeds limit ({max_hours}h)",
                employee_id=employee_id,
                shift_ids=[s.id for s in week_shifts]
            ))
    
    return conflicts


from datetime import timedelta


@router.get("", response_model=ShiftListResponse)
async def get_shifts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=1000),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    employee_id: Optional[int] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of shifts"""
    query = db.query(Shift)
    
    if start_date:
        query = query.filter(Shift.start_time >= datetime.combine(start_date, datetime.min.time()))
    
    if end_date:
        query = query.filter(Shift.start_time <= datetime.combine(end_date, datetime.max.time()))
    
    if employee_id:
        query = query.filter(Shift.employee_id == employee_id)
    
    if department_id:
        query = query.filter(Shift.department_id == department_id)
    
    query = query.order_by(Shift.start_time.desc())
    
    total = query.count()
    total_pages = ceil(total / page_size)
    
    shifts = query.offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for shift in shifts:
        items.append(ShiftResponse(
            id=shift.id,
            employee_id=shift.employee_id,
            employee_name=shift.employee.name if shift.employee else None,
            department_id=shift.department_id,
            department_name=shift.department.name if shift.department else None,
            start_time=shift.start_time,
            end_time=shift.end_time,
            status=shift.status,
            created_at=shift.created_at,
            updated_at=shift.updated_at
        ))
    
    return ShiftListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/conflicts", response_model=List[ShiftConflict])
async def get_conflicts(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get shift conflicts for a date range"""
    conflicts = []
    
    # Get all employees
    employees = db.query(Employee).all()
    
    for employee in employees:
        # Get shifts for this employee in the date range
        shifts = db.query(Shift).filter(
            Shift.employee_id == employee.id,
            Shift.status != "cancelled",
            Shift.start_time >= datetime.combine(start_date, datetime.min.time()),
            Shift.start_time <= datetime.combine(end_date, datetime.max.time())
        ).order_by(Shift.start_time).all()
        
        # Check for overlaps
        for i, shift1 in enumerate(shifts):
            for shift2 in shifts[i+1:]:
                if shift1.end_time > shift2.start_time:
                    conflicts.append(ShiftConflict(
                        type="overlap",
                        message=f"{employee.name} has overlapping shifts",
                        employee_id=employee.id,
                        shift_ids=[shift1.id, shift2.id]
                    ))
        
        # Check weekly hours
        total_hours = sum(
            (s.end_time - s.start_time).total_seconds() / 3600 
            for s in shifts
        )
        max_hours = employee.weekly_working_limit + employee.overtime_limit
        
        if total_hours > max_hours:
            conflicts.append(ShiftConflict(
                type="overtime",
                message=f"{employee.name} exceeds weekly limit ({total_hours:.1f}h / {max_hours}h)",
                employee_id=employee.id,
                shift_ids=[s.id for s in shifts]
            ))
    
    return conflicts


@router.get("/{shift_id}", response_model=ShiftResponse)
async def get_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get shift by ID"""
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )
    
    return ShiftResponse(
        id=shift.id,
        employee_id=shift.employee_id,
        employee_name=shift.employee.name if shift.employee else None,
        department_id=shift.department_id,
        department_name=shift.department.name if shift.department else None,
        start_time=shift.start_time,
        end_time=shift.end_time,
        status=shift.status,
        created_at=shift.created_at,
        updated_at=shift.updated_at
    )


@router.post("", response_model=ShiftResponse)
async def create_shift(
    shift_data: ShiftCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create a new shift"""
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
    
    # Check for conflicts (warning only, don't block)
    conflicts = check_shift_conflicts(
        db, shift_data.employee_id, shift_data.start_time, shift_data.end_time
    )
    
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


@router.put("/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: int,
    shift_data: ShiftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Update a shift"""
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )
    
    update_data = shift_data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(shift, key, value)
    
    db.commit()
    db.refresh(shift)
    
    return ShiftResponse(
        id=shift.id,
        employee_id=shift.employee_id,
        employee_name=shift.employee.name if shift.employee else None,
        department_id=shift.department_id,
        department_name=shift.department.name if shift.department else None,
        start_time=shift.start_time,
        end_time=shift.end_time,
        status=shift.status,
        created_at=shift.created_at,
        updated_at=shift.updated_at
    )


@router.delete("/{shift_id}")
async def delete_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Delete a shift"""
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )
    
    db.delete(shift)
    db.commit()
    
    return {"message": "Shift deleted successfully"}


@router.post("/bulk", response_model=ShiftBulkResponse)
async def create_shifts_bulk(
    bulk_data: ShiftBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create multiple shifts in a single transaction (optimized for AI optimization)"""
    created_count = 0
    failed_count = 0
    
    # Validate all employees and departments exist first
    employee_ids = set(s.employee_id for s in bulk_data.shifts)
    department_ids = set(s.department_id for s in bulk_data.shifts)
    
    existing_employees = {e.id for e in db.query(Employee.id).filter(Employee.id.in_(employee_ids)).all()}
    existing_departments = {d.id for d in db.query(Department.id).filter(Department.id.in_(department_ids)).all()}
    
    # Create shifts in bulk
    shifts_to_create = []
    for shift_data in bulk_data.shifts:
        if shift_data.employee_id not in existing_employees:
            failed_count += 1
            continue
        if shift_data.department_id not in existing_departments:
            failed_count += 1
            continue
            
        shifts_to_create.append(Shift(
            employee_id=shift_data.employee_id,
            department_id=shift_data.department_id,
            start_time=shift_data.start_time,
            end_time=shift_data.end_time,
            status=shift_data.status
        ))
    
    # Bulk insert
    if shifts_to_create:
        db.bulk_save_objects(shifts_to_create)
        db.commit()
        created_count = len(shifts_to_create)
    
    return ShiftBulkResponse(
        created_count=created_count,
        failed_count=failed_count,
        message=f"{created_count} vardiya başarıyla oluşturuldu"
    )
