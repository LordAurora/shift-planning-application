from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.shift_rule import ShiftRule
from app.models.department import Department
from app.models.user import User
from app.schemas.shift_rule import (
    ShiftRuleCreate,
    ShiftRuleUpdate,
    ShiftRuleResponse
)
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/rules", tags=["Shift Rules"])


@router.get("", response_model=List[ShiftRuleResponse])
async def get_rules(
    department_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all shift rules"""
    query = db.query(ShiftRule)
    
    if department_id:
        query = query.filter(ShiftRule.department_id == department_id)
    
    if is_active is not None:
        query = query.filter(ShiftRule.is_active == is_active)
    
    rules = query.all()
    
    return [
        ShiftRuleResponse(
            id=rule.id,
            name=rule.name,
            department_id=rule.department_id,
            department_name=rule.department.name if rule.department else None,
            role=rule.role,
            start_time=rule.start_time,
            end_time=rule.end_time,
            min_employees=rule.min_employees,
            max_employees=rule.max_employees,
            days_of_week=rule.days_of_week or [],
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at
        )
        for rule in rules
    ]


@router.get("/{rule_id}", response_model=ShiftRuleResponse)
async def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get shift rule by ID"""
    rule = db.query(ShiftRule).filter(ShiftRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift rule not found"
        )
    
    return ShiftRuleResponse(
        id=rule.id,
        name=rule.name,
        department_id=rule.department_id,
        department_name=rule.department.name if rule.department else None,
        role=rule.role,
        start_time=rule.start_time,
        end_time=rule.end_time,
        min_employees=rule.min_employees,
        max_employees=rule.max_employees,
        days_of_week=rule.days_of_week or [],
        is_active=rule.is_active,
        created_at=rule.created_at,
        updated_at=rule.updated_at
    )


@router.post("", response_model=ShiftRuleResponse)
async def create_rule(
    rule_data: ShiftRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create a new shift rule"""
    # Validate department exists
    department = db.query(Department).filter(Department.id == rule_data.department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department not found"
        )
    
    rule = ShiftRule(
        name=rule_data.name,
        department_id=rule_data.department_id,
        role=rule_data.role,
        start_time=rule_data.start_time,
        end_time=rule_data.end_time,
        min_employees=rule_data.min_employees,
        max_employees=rule_data.max_employees,
        days_of_week=rule_data.days_of_week,
        is_active=rule_data.is_active
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return ShiftRuleResponse(
        id=rule.id,
        name=rule.name,
        department_id=rule.department_id,
        department_name=department.name,
        role=rule.role,
        start_time=rule.start_time,
        end_time=rule.end_time,
        min_employees=rule.min_employees,
        max_employees=rule.max_employees,
        days_of_week=rule.days_of_week or [],
        is_active=rule.is_active,
        created_at=rule.created_at,
        updated_at=rule.updated_at
    )


@router.put("/{rule_id}", response_model=ShiftRuleResponse)
async def update_rule(
    rule_id: int,
    rule_data: ShiftRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Update a shift rule"""
    rule = db.query(ShiftRule).filter(ShiftRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift rule not found"
        )
    
    update_data = rule_data.model_dump(exclude_unset=True)
    
    # Validate department if being updated
    if "department_id" in update_data:
        department = db.query(Department).filter(Department.id == update_data["department_id"]).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )
    
    for key, value in update_data.items():
        setattr(rule, key, value)
    
    db.commit()
    db.refresh(rule)
    
    return ShiftRuleResponse(
        id=rule.id,
        name=rule.name,
        department_id=rule.department_id,
        department_name=rule.department.name if rule.department else None,
        role=rule.role,
        start_time=rule.start_time,
        end_time=rule.end_time,
        min_employees=rule.min_employees,
        max_employees=rule.max_employees,
        days_of_week=rule.days_of_week or [],
        is_active=rule.is_active,
        created_at=rule.created_at,
        updated_at=rule.updated_at
    )


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Delete a shift rule"""
    rule = db.query(ShiftRule).filter(ShiftRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift rule not found"
        )
    
    db.delete(rule)
    db.commit()
    
    return {"message": "Shift rule deleted successfully"}
