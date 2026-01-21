"""
Leave Processing Service - Handles leave request workflow and automation triggers.
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Optional, Tuple
from enum import Enum
import logging

from app.domain.models.leave import LeaveRequestEntity, LeaveStatus, LeaveDecision, LeaveBalance
from app.domain.models.employee import EmployeeEntity
from app.domain.models.shift import ShiftEntity, ShiftStatus

logger = logging.getLogger(__name__)


class AutomationTrigger(str, Enum):
    """Events that trigger automation"""
    LEAVE_APPROVED = "leave_approved"
    LEAVE_REJECTED = "leave_rejected"
    SICK_LEAVE_SUBMITTED = "sick_leave_submitted"
    EMERGENCY_LEAVE = "emergency_leave"
    CONFLICT_DETECTED = "conflict_detected"


@dataclass
class LeaveProcessingResult:
    """Result of leave request processing"""
    request: LeaveRequestEntity
    decision: LeaveDecision
    auto_processed: bool
    triggers_fired: List[AutomationTrigger]
    affected_shifts: List[int]  # shift IDs
    notifications_to_send: List[dict]
    explanation: str


@dataclass
class ConflictAnalysis:
    """Analysis of conflicts caused by a leave request"""
    has_conflicts: bool
    affected_shifts: List[ShiftEntity]
    critical_shifts: List[ShiftEntity]  # Shifts with no backup coverage
    coverage_percentage: float  # How much of the period has backup
    can_auto_resolve: bool
    resolution_suggestion: Optional[str]


class LeaveProcessingService:
    """
    Handles the complete leave request lifecycle.
    Integrates with shift optimization for automatic rebalancing.
    """
    
    def __init__(self, shift_optimization_service=None):
        self.shift_optimizer = shift_optimization_service
    
    def process_leave_request(
        self,
        request: LeaveRequestEntity,
        employee: EmployeeEntity,
        leave_balances: List[LeaveBalance],
        existing_shifts: List[ShiftEntity],
        all_employees: List[EmployeeEntity],
        approver_id: Optional[int] = None
    ) -> LeaveProcessingResult:
        """
        Process a leave request through the complete workflow.
        May result in auto-approval or queuing for manual review.
        """
        triggers_fired = []
        notifications = []
        
        # Validate request
        validation_errors = request.validate()
        if validation_errors:
            return LeaveProcessingResult(
                request=request,
                decision=LeaveDecision(
                    decision=LeaveStatus.REJECTED,
                    decided_by=0,
                    decided_at=datetime.now(),
                    reason="; ".join(validation_errors),
                    auto_decided=True
                ),
                auto_processed=True,
                triggers_fired=[],
                affected_shifts=[],
                notifications_to_send=[{
                    "type": "leave_rejected",
                    "recipient_id": request.employee_id,
                    "message": f"Leave request rejected: {validation_errors[0]}"
                }],
                explanation=f"Request failed validation: {validation_errors}"
            )
        
        # Check leave balance
        balance = next((b for b in leave_balances if b.leave_type == request.leave_type), None)
        balance_sufficient = balance and balance.available_days >= request.total_days
        
        # Analyze shift conflicts
        conflict_analysis = self._analyze_conflicts(request, employee, existing_shifts, all_employees)
        
        # Determine if auto-approval is possible
        can_auto, auto_reason = request.can_be_auto_approved(
            conflict_analysis.has_conflicts, balance_sufficient
        )
        
        if can_auto:
            # Auto-approve
            decision = LeaveDecision(
                decision=LeaveStatus.APPROVED,
                decided_by=0,  # System
                decided_at=datetime.now(),
                reason=auto_reason,
                auto_decided=True,
                shifts_affected=[s.id for s in conflict_analysis.affected_shifts],
                rebalance_required=conflict_analysis.has_conflicts
            )
            
            triggers_fired.append(AutomationTrigger.LEAVE_APPROVED)
            
            if request.leave_type.value == "sick":
                triggers_fired.append(AutomationTrigger.SICK_LEAVE_SUBMITTED)
            
            notifications.append({
                "type": "leave_approved",
                "recipient_id": request.employee_id,
                "message": f"Your {request.leave_type.value} leave request has been automatically approved"
            })
            
            # Notify managers of affected shifts
            if conflict_analysis.affected_shifts:
                notifications.append({
                    "type": "shifts_need_coverage",
                    "recipient_role": "manager",
                    "message": f"Employee {employee.name} approved for leave. {len(conflict_analysis.affected_shifts)} shifts need coverage."
                })
            
            explanation = f"Auto-approved: {auto_reason}"
            
        else:
            # Queue for manual review
            decision = LeaveDecision(
                decision=LeaveStatus.PENDING,
                decided_by=0,
                decided_at=datetime.now(),
                reason=auto_reason,
                auto_decided=False,
                shifts_affected=[s.id for s in conflict_analysis.affected_shifts],
                rebalance_required=conflict_analysis.has_conflicts
            )
            
            notifications.append({
                "type": "leave_pending_review",
                "recipient_role": "manager",
                "message": f"Leave request from {employee.name} requires review: {auto_reason}"
            })
            
            explanation = f"Queued for review: {auto_reason}"
            
            if conflict_analysis.has_conflicts:
                triggers_fired.append(AutomationTrigger.CONFLICT_DETECTED)
        
        request.status = decision.decision
        request.decision = decision
        
        return LeaveProcessingResult(
            request=request,
            decision=decision,
            auto_processed=can_auto,
            triggers_fired=triggers_fired,
            affected_shifts=[s.id for s in conflict_analysis.affected_shifts],
            notifications_to_send=notifications,
            explanation=explanation
        )
    
    def _analyze_conflicts(
        self,
        request: LeaveRequestEntity,
        employee: EmployeeEntity,
        existing_shifts: List[ShiftEntity],
        all_employees: List[EmployeeEntity]
    ) -> ConflictAnalysis:
        """Analyze what shifts are affected by this leave request"""
        
        leave_dates = request.get_affected_dates()
        
        # Find employee's shifts during leave period
        affected_shifts = [
            s for s in existing_shifts
            if s.employee_id == employee.id
            and s.start_time.date() in leave_dates
            and s.status == ShiftStatus.SCHEDULED
        ]
        
        if not affected_shifts:
            return ConflictAnalysis(
                has_conflicts=False,
                affected_shifts=[],
                critical_shifts=[],
                coverage_percentage=1.0,
                can_auto_resolve=True,
                resolution_suggestion=None
            )
        
        # Check if other employees can cover
        critical_shifts = []
        for shift in affected_shifts:
            # Find employees who could cover this shift
            potential_covers = [
                e for e in all_employees
                if e.id != employee.id
                and e.is_active
                and not e.is_on_leave
                and e.department_id == employee.department_id
                and e.can_work_shift(shift.duration_hours)[0]
            ]
            
            if not potential_covers:
                critical_shifts.append(shift)
        
        coverage = (len(affected_shifts) - len(critical_shifts)) / len(affected_shifts) if affected_shifts else 1.0
        
        resolution = None
        if critical_shifts:
            resolution = f"{len(critical_shifts)} shifts have no available backup. Consider hiring temp staff or extending shifts."
        elif affected_shifts:
            resolution = f"All {len(affected_shifts)} affected shifts can be covered by existing staff."
        
        return ConflictAnalysis(
            has_conflicts=len(affected_shifts) > 0,
            affected_shifts=affected_shifts,
            critical_shifts=critical_shifts,
            coverage_percentage=coverage,
            can_auto_resolve=len(critical_shifts) == 0,
            resolution_suggestion=resolution
        )
    
    def approve_leave(
        self,
        request: LeaveRequestEntity,
        approver_id: int,
        reason: str = "Manually approved"
    ) -> LeaveDecision:
        """Manually approve a leave request"""
        decision = LeaveDecision(
            decision=LeaveStatus.APPROVED,
            decided_by=approver_id,
            decided_at=datetime.now(),
            reason=reason,
            auto_decided=False,
            rebalance_required=True
        )
        
        request.status = LeaveStatus.APPROVED
        request.decision = decision
        
        logger.info(f"Leave request {request.id} approved by user {approver_id}")
        
        return decision
    
    def reject_leave(
        self,
        request: LeaveRequestEntity,
        rejector_id: int,
        reason: str
    ) -> LeaveDecision:
        """Manually reject a leave request"""
        decision = LeaveDecision(
            decision=LeaveStatus.REJECTED,
            decided_by=rejector_id,
            decided_at=datetime.now(),
            reason=reason,
            auto_decided=False
        )
        
        request.status = LeaveStatus.REJECTED
        request.decision = decision
        
        logger.info(f"Leave request {request.id} rejected by user {rejector_id}: {reason}")
        
        return decision
    
    def get_leave_balance(
        self,
        employee_id: int,
        leave_type: str,
        year: int = None
    ) -> LeaveBalance:
        """
        Calculate employee's leave balance.
        In production, this would query the database.
        """
        if year is None:
            year = datetime.now().year
        
        # Default annual leave allowances (would come from DB/config)
        allowances = {
            "annual": 14,  # 14 days annual leave
            "sick": 10,    # 10 days sick leave
            "personal": 5, # 5 days personal leave
            "maternity": 112,  # 16 weeks
            "paternity": 10,
            "unpaid": 30,
        }
        
        total = allowances.get(leave_type, 0)
        
        # Used/pending would come from database
        used = 0.0
        pending = 0.0
        
        return LeaveBalance(
            leave_type=leave_type,
            total_days=total,
            used_days=used,
            pending_days=pending
        )
