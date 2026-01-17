from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, time


class ShiftRuleBase(BaseModel):
    name: str
    department_id: int
    role: str
    start_time: time
    end_time: time
    min_employees: int = 1
    max_employees: int = 10
    days_of_week: List[int] = [1, 2, 3, 4, 5]
    is_active: bool = True


class ShiftRuleCreate(ShiftRuleBase):
    pass


class ShiftRuleUpdate(BaseModel):
    name: Optional[str] = None
    department_id: Optional[int] = None
    role: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    min_employees: Optional[int] = None
    max_employees: Optional[int] = None
    days_of_week: Optional[List[int]] = None
    is_active: Optional[bool] = None


class ShiftRuleResponse(ShiftRuleBase):
    id: int
    department_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
