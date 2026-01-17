from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ShiftStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ShiftBase(BaseModel):
    employee_id: int
    department_id: int
    start_time: datetime
    end_time: datetime
    status: ShiftStatus = ShiftStatus.SCHEDULED


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(BaseModel):
    employee_id: Optional[int] = None
    department_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[ShiftStatus] = None


class ShiftResponse(ShiftBase):
    id: int
    employee_name: Optional[str] = None
    department_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShiftListResponse(BaseModel):
    items: List[ShiftResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ShiftConflict(BaseModel):
    type: str  # "overlap", "overtime", "availability"
    message: str
    employee_id: int
    shift_ids: List[int]


class ShiftBulkCreate(BaseModel):
    shifts: List[ShiftCreate]


class ShiftBulkResponse(BaseModel):
    created_count: int
    failed_count: int
    message: str
