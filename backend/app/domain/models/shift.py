"""
Pure domain entity for Shift - Framework agnostic business logic.
This represents the core business rules without any database/framework dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List


class ShiftConflictType(str, Enum):
    """Types of conflicts that can occur with shifts"""
    OVERLAP = "overlap"
    OVERTIME_EXCEEDED = "overtime_exceeded"
    REST_PERIOD_VIOLATION = "rest_period_violation"
    AVAILABILITY_MISMATCH = "availability_mismatch"
    CONSECUTIVE_DAYS_EXCEEDED = "consecutive_days_exceeded"
    SKILL_MISMATCH = "skill_mismatch"


class ShiftStatus(str, Enum):
    """Shift lifecycle states"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ShiftConflict:
    """Represents a detected conflict for a shift"""
    type: ShiftConflictType
    message: str
    severity: str  # "error" | "warning"
    affected_shift_ids: List[int] = field(default_factory=list)
    resolution_suggestion: Optional[str] = None


@dataclass
class ShiftAssignment:
    """Represents the assignment decision for a shift"""
    employee_id: int
    shift_id: int
    assigned_at: datetime
    assigned_by: int  # user_id who made the assignment
    assignment_reason: str  # AI/manual/rule-based
    confidence_score: Optional[float] = None  # AI confidence if AI-assigned
    explanation: Optional[str] = None  # Why this employee was chosen


@dataclass
class ShiftEntity:
    """
    Pure domain model for a Shift.
    Contains business logic and validation rules without database concerns.
    """
    id: Optional[int]
    employee_id: int
    department_id: int
    start_time: datetime
    end_time: datetime
    status: ShiftStatus = ShiftStatus.SCHEDULED
    created_by: Optional[int] = None
    
    # Business rule constants
    MIN_SHIFT_DURATION_HOURS: float = 4.0
    MAX_SHIFT_DURATION_HOURS: float = 12.0
    MIN_REST_BETWEEN_SHIFTS_HOURS: float = 11.0
    MAX_CONSECUTIVE_WORKING_DAYS: int = 6
    
    @property
    def duration_hours(self) -> float:
        """Calculate shift duration in hours"""
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600
    
    @property
    def is_overnight(self) -> bool:
        """Check if shift spans midnight"""
        return self.end_time.date() > self.start_time.date()
    
    @property
    def is_active(self) -> bool:
        """Check if shift is currently in progress"""
        now = datetime.now(self.start_time.tzinfo)
        return self.start_time <= now <= self.end_time and self.status == ShiftStatus.SCHEDULED
    
    def validate(self) -> List[ShiftConflict]:
        """
        Validate shift against business rules.
        Returns list of conflicts/violations.
        """
        conflicts = []
        
        # Duration validation
        if self.duration_hours < self.MIN_SHIFT_DURATION_HOURS:
            conflicts.append(ShiftConflict(
                type=ShiftConflictType.OVERLAP,
                message=f"Shift duration ({self.duration_hours:.1f}h) is below minimum ({self.MIN_SHIFT_DURATION_HOURS}h)",
                severity="error"
            ))
        
        if self.duration_hours > self.MAX_SHIFT_DURATION_HOURS:
            conflicts.append(ShiftConflict(
                type=ShiftConflictType.OVERTIME_EXCEEDED,
                message=f"Shift duration ({self.duration_hours:.1f}h) exceeds maximum ({self.MAX_SHIFT_DURATION_HOURS}h)",
                severity="error"
            ))
        
        # Time ordering
        if self.end_time <= self.start_time:
            conflicts.append(ShiftConflict(
                type=ShiftConflictType.OVERLAP,
                message="End time must be after start time",
                severity="error"
            ))
        
        return conflicts
    
    def overlaps_with(self, other: "ShiftEntity") -> bool:
        """Check if this shift overlaps with another"""
        return (self.start_time < other.end_time and self.end_time > other.start_time)
    
    def check_rest_period(self, previous_shift: "ShiftEntity") -> Optional[ShiftConflict]:
        """
        Check if minimum rest period is maintained between shifts.
        Returns conflict if violated.
        """
        rest_hours = (self.start_time - previous_shift.end_time).total_seconds() / 3600
        
        if rest_hours < self.MIN_REST_BETWEEN_SHIFTS_HOURS:
            return ShiftConflict(
                type=ShiftConflictType.REST_PERIOD_VIOLATION,
                message=f"Rest period ({rest_hours:.1f}h) is below minimum ({self.MIN_REST_BETWEEN_SHIFTS_HOURS}h)",
                severity="error",
                resolution_suggestion=f"Move shift start to at least {previous_shift.end_time + timedelta(hours=self.MIN_REST_BETWEEN_SHIFTS_HOURS)}"
            )
        return None
    
    def can_be_cancelled(self) -> bool:
        """Check if shift can be cancelled based on business rules"""
        if self.status in [ShiftStatus.COMPLETED, ShiftStatus.CANCELLED]:
            return False
        if self.status == ShiftStatus.IN_PROGRESS:
            return False
        return True
    
    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "department_id": self.department_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "status": self.status.value,
            "duration_hours": self.duration_hours,
            "is_overnight": self.is_overnight,
        }
