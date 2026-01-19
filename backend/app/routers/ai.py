from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import random
from app.database import get_db
from app.models.shift import Shift
from app.models.shift_rule import ShiftRule
from app.models.employee import Employee
from app.models.department import Department
from app.models.user import User
from app.schemas.ai import OptimizationRequest, OptimizationResult, ApplyOptimizationRequest
from app.schemas.shift import ShiftResponse, ShiftConflict, ShiftStatus
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/ai", tags=["AI Optimization"])


def generate_optimized_shifts(
    db: Session,
    start_date: datetime,
    end_date: datetime,
    department_ids: List[int] = None
) -> tuple[List[dict], List[ShiftConflict], float]:
    """
    Generate optimized shifts based on rules and employee availability.
    
    This is a placeholder implementation that demonstrates the API structure.
    In production, this would integrate with an actual AI/optimization engine.
    """
    shifts = []
    conflicts = []
    
    # Get active rules
    rules_query = db.query(ShiftRule).filter(ShiftRule.is_active == True)
    if department_ids:
        rules_query = rules_query.filter(ShiftRule.department_id.in_(department_ids))
    rules = rules_query.all()
    
    # Get employees
    employees_query = db.query(Employee)
    if department_ids:
        employees_query = employees_query.filter(Employee.department_id.in_(department_ids))
    employees = employees_query.all()
    
    if not employees:
        return [], [], 0.0
    
    # Track weekly hours per employee
    employee_hours = {emp.id: 0.0 for emp in employees}
    
    shift_id_counter = 1000
    current_date = start_date
    
    while current_date <= end_date:
        day_of_week = current_date.weekday()
        # Convert Python weekday (0=Monday) to our format (0=Sunday)
        day_of_week_adjusted = (day_of_week + 1) % 7
        
        for rule in rules:
            if day_of_week_adjusted not in (rule.days_of_week or []):
                continue
            
            # Find eligible employees for this rule
            eligible_employees = [
                emp for emp in employees
                if emp.department_id == rule.department_id
                and (rule.role == "Any" or emp.role == rule.role)
            ]
            
            if not eligible_employees:
                continue
            
            # Calculate shift duration
            shift_start = datetime.combine(current_date.date(), rule.start_time)
            shift_end = datetime.combine(current_date.date(), rule.end_time)
            if rule.end_time < rule.start_time:
                shift_end += timedelta(days=1)
            shift_duration = (shift_end - shift_start).total_seconds() / 3600
            
            # Assign employees (simplified logic)
            num_to_assign = random.randint(rule.min_employees, rule.max_employees)
            assigned = 0
            
            # Sort by hours worked (assign to those with fewer hours first)
            sorted_employees = sorted(eligible_employees, key=lambda e: employee_hours[e.id])
            
            for emp in sorted_employees:
                if assigned >= num_to_assign:
                    break
                
                # Check if employee would exceed weekly limit
                potential_hours = employee_hours[emp.id] + shift_duration
                max_hours = emp.weekly_working_limit + emp.overtime_limit
                
                if potential_hours > max_hours:
                    continue
                
                # Check availability (simplified - just check day of week)
                available_days = [slot.get('day') for slot in (emp.availability or [])]
                if available_days and day_of_week_adjusted not in available_days:
                    continue
                
                # Create shift
                department = db.query(Department).filter(Department.id == emp.department_id).first()
                
                shift_data = {
                    "id": shift_id_counter,
                    "employee_id": emp.id,
                    "employee_name": emp.name,
                    "department_id": emp.department_id,
                    "department_name": department.name if department else None,
                    "start_time": shift_start,
                    "end_time": shift_end,
                    "status": ShiftStatus.SCHEDULED,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                shifts.append(shift_data)
                
                employee_hours[emp.id] += shift_duration
                shift_id_counter += 1
                assigned += 1
                
                # Check for overtime warning
                if employee_hours[emp.id] > emp.weekly_working_limit:
                    overtime = employee_hours[emp.id] - emp.weekly_working_limit
                    if overtime > 0:
                        conflicts.append(ShiftConflict(
                            type="overtime",
                            message=f"{emp.name} has {overtime:.1f}h overtime this period",
                            employee_id=emp.id,
                            shift_ids=[shift_id_counter - 1]
                        ))
        
        current_date += timedelta(days=1)
    
    # Calculate optimization score (simplified)
    # Higher score = better distribution of shifts
    if not shifts:
        optimization_score = 0.0
    else:
        # Score based on how evenly shifts are distributed
        total_employees = len(employees)
        shifts_per_employee = len(shifts) / max(total_employees, 1)
        variance = sum((employee_hours[emp.id] - sum(employee_hours.values()) / max(total_employees, 1)) ** 2 
                      for emp in employees) / max(total_employees, 1)
        optimization_score = max(0, min(100, 100 - variance))
    
    return shifts, conflicts, optimization_score


@router.post("/optimize", response_model=OptimizationResult)
async def optimize_shifts(
    request: OptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """
    Generate optimized shift schedule using AI.
    
    This endpoint analyzes employee availability, shift rules, and constraints
    to produce an optimal shift schedule for the specified date range.
    """
    start_datetime = datetime.combine(request.start_date, datetime.min.time())
    end_datetime = datetime.combine(request.end_date, datetime.max.time())
    
    shifts, conflicts, score = generate_optimized_shifts(
        db,
        start_datetime,
        end_datetime,
        request.department_ids
    )
    
    # Convert to response format
    shift_responses = [ShiftResponse(**shift) for shift in shifts]
    
    return OptimizationResult(
        shifts=shift_responses,
        conflicts=conflicts,
        optimization_score=round(score, 1),
        message=f"Generated {len(shifts)} shifts with {len(conflicts)} warning(s)."
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
    created_shifts = []
    
    for shift_data in request.shifts:
        # Create actual shift in database
        shift = Shift(
            employee_id=shift_data.employee_id,
            department_id=shift_data.department_id,
            start_time=shift_data.start_time,
            end_time=shift_data.end_time,
            status=shift_data.status
        )
        
        db.add(shift)
        created_shifts.append(shift)
    
    db.commit()
    
    # Refresh to get IDs
    for shift in created_shifts:
        db.refresh(shift)
    
    return {
        "message": f"Successfully created {len(created_shifts)} shifts",
        "shift_ids": [shift.id for shift in created_shifts]
    }
