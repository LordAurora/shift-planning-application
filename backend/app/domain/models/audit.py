"""
Audit Trail Domain Model - Immutable audit entries for compliance and tracking.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json
import hashlib


class AuditAction(str, Enum):
    """Types of auditable actions"""
    # Shift actions
    SHIFT_CREATED = "shift.created"
    SHIFT_UPDATED = "shift.updated"
    SHIFT_DELETED = "shift.deleted"
    SHIFT_ASSIGNED = "shift.assigned"
    SHIFT_CANCELLED = "shift.cancelled"
    SHIFT_SWAPPED = "shift.swapped"
    
    # Leave actions
    LEAVE_REQUESTED = "leave.requested"
    LEAVE_APPROVED = "leave.approved"
    LEAVE_REJECTED = "leave.rejected"
    LEAVE_CANCELLED = "leave.cancelled"
    
    # Employee actions
    EMPLOYEE_CREATED = "employee.created"
    EMPLOYEE_UPDATED = "employee.updated"
    EMPLOYEE_DEACTIVATED = "employee.deactivated"
    
    # AI/Automation actions
    AI_OPTIMIZATION_RUN = "ai.optimization_run"
    AI_SUGGESTION_GENERATED = "ai.suggestion_generated"
    AUTO_REBALANCE_TRIGGERED = "auto.rebalance_triggered"
    AUTO_APPROVAL_EXECUTED = "auto.approval_executed"
    
    # Auth actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_PASSWORD_CHANGED = "user.password_changed"
    PERMISSION_CHANGED = "permission.changed"
    
    # System actions
    SYSTEM_CONFIG_CHANGED = "system.config_changed"
    BULK_OPERATION = "system.bulk_operation"


class AuditSeverity(str, Enum):
    """Severity/importance of audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """
    Immutable audit log entry.
    Designed for append-only storage with integrity verification.
    """
    id: Optional[int]
    
    # Who performed the action (required first to satisfy dataclass ordering)
    actor_id: int  # user_id
    actor_email: str
    actor_role: str

    # What action was performed (required)
    action: AuditAction

    # On which resource (required)
    resource_type: str  # "shift", "leave", "employee", etc.

    # Optional actor context
    actor_ip: Optional[str] = None
    actor_user_agent: Optional[str] = None

    # Optional severity and resource identifiers
    severity: AuditSeverity = AuditSeverity.MEDIUM
    resource_id: Optional[int] = None
    
    # Change details
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = None  # Human-readable summary
    
    # Context
    reason: Optional[str] = None  # Why the change was made
    correlation_id: Optional[str] = None  # For tracing related operations
    triggered_by: Optional[str] = None  # What triggered this (user/automation/ai)
    
    # Timestamps
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Integrity
    checksum: Optional[str] = None  # SHA256 of entry for tamper detection
    previous_checksum: Optional[str] = None  # Chain to previous entry
    
    def __post_init__(self):
        """Calculate checksum after initialization"""
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate SHA256 checksum for integrity verification"""
        data = {
            "actor_id": self.actor_id,
            "action": self.action.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "timestamp": self.timestamp.isoformat(),
            "previous_checksum": self.previous_checksum,
        }
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify that the entry hasn't been tampered with"""
        return self.checksum == self._calculate_checksum()
    
    @property
    def changes(self) -> Dict[str, tuple]:
        """
        Get dictionary of changed fields.
        Returns {field_name: (old_value, new_value)}
        """
        if not self.before_state or not self.after_state:
            return {}
        
        changes = {}
        all_keys = set(self.before_state.keys()) | set(self.after_state.keys())
        
        for key in all_keys:
            old_val = self.before_state.get(key)
            new_val = self.after_state.get(key)
            if old_val != new_val:
                changes[key] = (old_val, new_val)
        
        return changes
    
    @property
    def is_sensitive(self) -> bool:
        """Check if this audit entry contains sensitive information"""
        sensitive_actions = [
            AuditAction.USER_PASSWORD_CHANGED,
            AuditAction.PERMISSION_CHANGED,
            AuditAction.USER_LOGIN,
        ]
        return self.action in sensitive_actions
    
    def generate_summary(self) -> str:
        """Generate human-readable summary of the action"""
        if self.change_summary:
            return self.change_summary
        
        action_descriptions = {
            AuditAction.SHIFT_CREATED: "created a shift",
            AuditAction.SHIFT_UPDATED: "updated a shift",
            AuditAction.SHIFT_DELETED: "deleted a shift",
            AuditAction.SHIFT_ASSIGNED: "assigned a shift",
            AuditAction.LEAVE_REQUESTED: "requested leave",
            AuditAction.LEAVE_APPROVED: "approved leave request",
            AuditAction.LEAVE_REJECTED: "rejected leave request",
            AuditAction.AI_OPTIMIZATION_RUN: "ran AI optimization",
        }
        
        action_desc = action_descriptions.get(self.action, self.action.value)
        resource_desc = f"{self.resource_type} #{self.resource_id}" if self.resource_id else self.resource_type
        
        return f"{self.actor_email} ({self.actor_role}) {action_desc} for {resource_desc}"
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for storage"""
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "actor_email": self.actor_email,
            "actor_role": self.actor_role,
            "actor_ip": self.actor_ip,
            "action": self.action.value,
            "severity": self.severity.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "change_summary": self.generate_summary(),
            "reason": self.reason,
            "correlation_id": self.correlation_id,
            "triggered_by": self.triggered_by,
            "timestamp": self.timestamp.isoformat(),
            "checksum": self.checksum,
        }


@dataclass
class AuditQuery:
    """Query parameters for audit log searches"""
    actor_id: Optional[int] = None
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    severity: Optional[AuditSeverity] = None
    correlation_id: Optional[str] = None
    limit: int = 100
    offset: int = 0
