"""
Pure domain entity for Leave Request - Framework agnostic business logic.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, List


class LeaveType(str, Enum):
    """Types of leave requests"""
    ANNUAL = "annual"
    SICK = "sick"
    PERSONAL = "personal"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    UNPAID = "unpaid"
    EMERGENCY = "emergency"
    BEREAVEMENT = "bereavement"


class LeaveStatus(str, Enum):
    """Leave request lifecycle states"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LeaveUrgency(str, Enum):
    """Urgency level for leave processing"""
    NORMAL = "normal"
    URGENT = "urgent"
    EMERGENCY = "emergency"


@dataclass
class LeaveDecision:
    """Represents the decision made on a leave request"""
    decision: LeaveStatus
    decided_by: int  # user_id
    decided_at: datetime
    reason: str
    auto_decided: bool = False  # Was this decided by automation?
    shifts_affected: List[int] = field(default_factory=list)
    rebalance_required: bool = False


@dataclass
class LeaveBalance:
    """Employee's leave balance"""
    leave_type: LeaveType
    total_days: float
    used_days: float
    pending_days: float  # Days in pending requests
    
    @property
    def available_days(self) -> float:
        return max(0, self.total_days - self.used_days - self.pending_days)


@dataclass
class LeaveRequestEntity:
    """
    Pure domain model for a Leave Request.
    Contains business logic for leave management.
    """
    id: Optional[int]
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str] = None
    status: LeaveStatus = LeaveStatus.PENDING
    urgency: LeaveUrgency = LeaveUrgency.NORMAL
    
    # Decision tracking
    decision: Optional[LeaveDecision] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Business rule constants
    MIN_ADVANCE_NOTICE_DAYS: int = 7  # For non-urgent requests
    MAX_CONSECUTIVE_LEAVE_DAYS: int = 30
    AUTO_APPROVE_THRESHOLD_DAYS: int = 2  # Auto-approve short leaves if no conflicts
    
    @property
    def total_days(self) -> int:
        """Calculate total leave days requested"""
        return (self.end_date - self.start_date).days + 1
    
    @property
    def is_short_leave(self) -> bool:
        """Check if this is a short leave (potential auto-approve candidate)"""
        return self.total_days <= self.AUTO_APPROVE_THRESHOLD_DAYS
    
    @property
    def is_future_request(self) -> bool:
        """Check if leave starts in the future"""
        return self.start_date > date.today()
    
    @property
    def advance_notice_days(self) -> int:
        """Days between request creation and leave start"""
        if not self.created_at:
            return 0
        return (self.start_date - self.created_at.date()).days
    
    def validate(self) -> List[str]:
        """
        Validate leave request against business rules.
        Returns list of validation errors.
        """
        errors = []
        
        # Date validation
        if self.end_date < self.start_date:
            errors.append("End date cannot be before start date")
        
        # Duration validation
        if self.total_days > self.MAX_CONSECUTIVE_LEAVE_DAYS:
            errors.append(f"Leave duration ({self.total_days} days) exceeds maximum ({self.MAX_CONSECUTIVE_LEAVE_DAYS} days)")
        
        # Advance notice for non-urgent requests
        if self.urgency == LeaveUrgency.NORMAL and self.is_future_request:
            if self.advance_notice_days < self.MIN_ADVANCE_NOTICE_DAYS:
                errors.append(f"Non-urgent leave requires {self.MIN_ADVANCE_NOTICE_DAYS} days advance notice")
        
        # Past date validation
        if self.start_date < date.today() and self.leave_type not in [LeaveType.SICK, LeaveType.EMERGENCY]:
            errors.append("Leave start date cannot be in the past for this leave type")
        
        return errors
    
    def can_be_auto_approved(self, has_conflicts: bool, balance_sufficient: bool) -> tuple[bool, str]:
        """
        Determine if this request can be auto-approved.
        Returns (can_auto_approve, reason)
        """
        if self.urgency == LeaveUrgency.EMERGENCY:
            return True, "Emergency leave auto-approved"
        
        if not balance_sufficient:
            return False, "Insufficient leave balance"
        
        if has_conflicts:
            return False, "Shift conflicts detected - requires manager review"
        
        if self.is_short_leave and self.leave_type == LeaveType.SICK:
            return True, "Short sick leave auto-approved"
        
        if self.total_days <= 1 and self.leave_type == LeaveType.PERSONAL:
            return True, "Single day personal leave auto-approved"
        
        return False, "Requires manager approval"
    
    def can_be_cancelled(self) -> tuple[bool, str]:
        """Check if leave can be cancelled"""
        if self.status == LeaveStatus.CANCELLED:
            return False, "Leave is already cancelled"
        
        if self.status == LeaveStatus.REJECTED:
            return False, "Rejected leave cannot be cancelled"
        
        if self.start_date <= date.today():
            if self.status == LeaveStatus.APPROVED:
                return False, "Cannot cancel approved leave that has started"
        
        return True, "OK"
    
    def get_affected_dates(self) -> List[date]:
        """Get list of all dates covered by this leave"""
        dates = []
        current = self.start_date
        while current <= self.end_date:
            dates.append(current)
            current = date.fromordinal(current.toordinal() + 1)
        return dates
    
    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "leave_type": self.leave_type.value,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_days": self.total_days,
            "reason": self.reason,
            "status": self.status.value,
            "urgency": self.urgency.value,
            "is_short_leave": self.is_short_leave,
        }
