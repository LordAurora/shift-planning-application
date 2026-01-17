from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from app.models.leave_request import LeaveType, LeaveStatus


class LeaveRequestBase(BaseModel):
    type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str] = None


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str]
    type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str]
    status: LeaveStatus
    response_note: Optional[str]
    responded_by: Optional[int]
    responder_name: Optional[str]
    responded_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
