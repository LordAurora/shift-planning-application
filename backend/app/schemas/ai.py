from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from app.schemas.shift import ShiftResponse, ShiftConflict


class OptimizationRequest(BaseModel):
    start_date: date
    end_date: date
    department_ids: Optional[List[int]] = None


class OptimizationResult(BaseModel):
    shifts: List[ShiftResponse]
    conflicts: List[ShiftConflict]
    optimization_score: float
    message: str


class ApplyOptimizationRequest(BaseModel):
    shifts: List[ShiftResponse]
