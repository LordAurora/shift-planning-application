from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from app.schemas.shift import ShiftResponse, ShiftConflict


class OptimizationSettings(BaseModel):
    shift_types: List[str] = Field(default_factory=lambda: ["morning", "day", "afternoon"])
    operating_days: List[str] = Field(
        default_factory=lambda: ["monday", "tuesday", "wednesday", "thursday", "friday"]
    )
    is_24_7: bool = False
    min_employees_per_shift: int = Field(2, ge=0, le=100)
    max_employees_per_shift: int = Field(10, ge=1, le=200)
    max_hours_per_week: float = Field(45, ge=1, le=80)
    max_consecutive_days: int = Field(5, ge=1, le=7)
    min_rest_hours: float = Field(11, ge=0, le=24)
    allow_overtime: bool = False
    consider_preferences: bool = True
    preference_weight: float = Field(70, ge=0, le=100)
    balance_workload: bool = True


class OptimizationRequest(BaseModel):
    start_date: date
    end_date: date
    department_ids: Optional[List[int]] = None
    settings: OptimizationSettings = Field(default_factory=OptimizationSettings)


class OptimizationMetrics(BaseModel):
    coverage: float
    preference_match: float
    fairness: float
    total_hours: float
    employees_scheduled: int


class OptimizedShift(ShiftResponse):
    shift_type: str
    preferred: bool = False


class OptimizationResult(BaseModel):
    shifts: List[OptimizedShift]
    conflicts: List[ShiftConflict]
    optimization_score: float
    metrics: Optional[OptimizationMetrics] = None
    message: str


class ApplyOptimizationRequest(BaseModel):
    shifts: List[ShiftResponse]
