from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from math import ceil
from passlib.context import CryptContext
from app.database import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.models.user import User, UserRole
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse,
    EmployeePreferences,
)
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/employees", tags=["Employees"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _employee_for_user(db: Session, user: User) -> Employee:
    employee = db.query(Employee).filter(Employee.email == user.email).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employee profile is linked to this account",
        )
    return employee


@router.get("/me/preferences", response_model=EmployeePreferences)
async def get_my_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scheduling preferences of the signed-in employee (used by the mobile app)."""
    employee = _employee_for_user(db, current_user)
    return EmployeePreferences(**(employee.preferences or {}))


@router.put("/me/preferences", response_model=EmployeePreferences)
async def update_my_preferences(
    preferences: EmployeePreferences,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the signed-in employee's preferences. The optimizer uses them on the next run."""
    employee = _employee_for_user(db, current_user)
    employee.preferences = preferences.model_dump()
    db.commit()
    return preferences


@router.get("", response_model=EmployeeListResponse)
async def get_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=1000),
    department_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of employees"""
    query = db.query(Employee)
    
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Employee.name.ilike(search_term)) | 
            (Employee.email.ilike(search_term))
        )
    
    total = query.count()
    total_pages = ceil(total / page_size)
    
    employees = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Add department names
    items = []
    for emp in employees:
        emp_dict = {
            "id": emp.id,
            "name": emp.name,
            "email": emp.email,
            "role": emp.role,
            "department_id": emp.department_id,
            "department_name": emp.department.name if emp.department else None,
            "availability": emp.availability or [],
            "weekly_working_limit": emp.weekly_working_limit,
            "overtime_limit": emp.overtime_limit,
            "preferences": emp.preferences or None,
            "created_at": emp.created_at,
            "updated_at": emp.updated_at
        }
        items.append(EmployeeResponse(**emp_dict))
    
    return EmployeeListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employee by ID"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return EmployeeResponse(
        id=employee.id,
        name=employee.name,
        email=employee.email,
        role=employee.role,
        department_id=employee.department_id,
        department_name=employee.department.name if employee.department else None,
        availability=employee.availability or [],
        weekly_working_limit=employee.weekly_working_limit,
        overtime_limit=employee.overtime_limit,
        preferences=employee.preferences or None,
        created_at=employee.created_at,
        updated_at=employee.updated_at
    )


@router.post("", response_model=EmployeeResponse)
async def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create a new employee with user account for mobile app login"""
    # Check if email already exists in employees
    existing_employee = db.query(Employee).filter(Employee.email == employee_data.email).first()
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee with this email already exists"
        )
    
    # Check if email already exists in users
    existing_user = db.query(User).filter(User.email == employee_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Check if department exists
    department = db.query(Department).filter(Department.id == employee_data.department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department not found"
        )
    
    # Hash the password
    hashed_password = pwd_context.hash(employee_data.password)
    
    # Create user account for mobile app login
    user = User(
        email=employee_data.email,
        name=employee_data.name,
        hashed_password=hashed_password,
        role=UserRole.EMPLOYEE,
        is_active=True
    )
    db.add(user)
    
    # Convert availability to dict format
    availability_data = [slot.model_dump() for slot in employee_data.availability]
    
    employee = Employee(
        name=employee_data.name,
        email=employee_data.email,
        role=employee_data.role,
        department_id=employee_data.department_id,
        availability=availability_data,
        weekly_working_limit=employee_data.weekly_working_limit,
        overtime_limit=employee_data.overtime_limit,
        preferences=employee_data.preferences.model_dump() if employee_data.preferences else {},
    )
    
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    return EmployeeResponse(
        id=employee.id,
        name=employee.name,
        email=employee.email,
        role=employee.role,
        department_id=employee.department_id,
        department_name=department.name,
        availability=employee.availability or [],
        weekly_working_limit=employee.weekly_working_limit,
        overtime_limit=employee.overtime_limit,
        preferences=employee.preferences or None,
        created_at=employee.created_at,
        updated_at=employee.updated_at
    )


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Update an employee and their user account"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    update_data = employee_data.model_dump(exclude_unset=True)
    
    # Handle password update for user account
    if "password" in update_data and update_data["password"]:
        user = db.query(User).filter(User.email == employee.email).first()
        if user:
            user.hashed_password = pwd_context.hash(update_data["password"])
        del update_data["password"]
    
    # Store preferences as plain JSON
    if "preferences" in update_data and update_data["preferences"] is not None:
        prefs = update_data["preferences"]
        update_data["preferences"] = prefs.model_dump() if hasattr(prefs, "model_dump") else prefs

    # Handle availability conversion
    if "availability" in update_data and update_data["availability"]:
        update_data["availability"] = [slot.model_dump() if hasattr(slot, 'model_dump') else slot for slot in update_data["availability"]]
    
    # Check department if being updated
    if "department_id" in update_data:
        department = db.query(Department).filter(Department.id == update_data["department_id"]).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )
    
    # Update user email/name if changed
    if "email" in update_data or "name" in update_data:
        user = db.query(User).filter(User.email == employee.email).first()
        if user:
            if "email" in update_data:
                user.email = update_data["email"]
            if "name" in update_data:
                user.name = update_data["name"]
    
    for key, value in update_data.items():
        setattr(employee, key, value)
    
    db.commit()
    db.refresh(employee)
    
    return EmployeeResponse(
        id=employee.id,
        name=employee.name,
        email=employee.email,
        role=employee.role,
        department_id=employee.department_id,
        department_name=employee.department.name if employee.department else None,
        availability=employee.availability or [],
        weekly_working_limit=employee.weekly_working_limit,
        overtime_limit=employee.overtime_limit,
        preferences=employee.preferences or None,
        created_at=employee.created_at,
        updated_at=employee.updated_at
    )


@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Delete an employee and their user account"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Delete associated user account
    user = db.query(User).filter(User.email == employee.email).first()
    if user:
        db.delete(user)
    
    db.delete(employee)
    db.commit()
    
    return {"message": "Employee deleted successfully"}
