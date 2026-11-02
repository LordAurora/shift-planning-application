from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional, List
from datetime import datetime


class AvailabilitySlot(BaseModel):
    day: int  # 0-6 (Sunday-Saturday)
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format


ShiftPreference = Literal["morning", "day", "afternoon", "night"]
WorkModel = Literal["office", "remote", "hybrid"]


class EmployeePreferences(BaseModel):
    preferred_shift: Optional[ShiftPreference] = None  # None = no preference
    weekly_off_day: Optional[int] = Field(None, ge=0, le=6)  # 0-6 (Sunday-Saturday)
    work_model: Optional[WorkModel] = None
    office_days: Optional[int] = Field(None, ge=0, le=7)
    remote_days: Optional[int] = Field(None, ge=0, le=7)
    notes: Optional[str] = Field(None, max_length=1000)


class EmployeeBase(BaseModel):
    name: str
    email: EmailStr
    role: str
    department_id: int
    availability: List[AvailabilitySlot] = []
    weekly_working_limit: float = 40.0
    overtime_limit: float = 10.0
    preferences: Optional[EmployeePreferences] = None


class EmployeeCreate(EmployeeBase):
    password: str  # Password for mobile app login


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    department_id: Optional[int] = None
    availability: Optional[List[AvailabilitySlot]] = None
    weekly_working_limit: Optional[float] = None
    overtime_limit: Optional[float] = None
    preferences: Optional[EmployeePreferences] = None
    password: Optional[str] = None  # Optional password update


class EmployeeResponse(EmployeeBase):
    id: int
    department_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    items: List[EmployeeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
