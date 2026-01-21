"""
Audit Service - Centralized audit logging with integrity verification.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
import json

from app.domain.models.audit import AuditEntry, AuditAction, AuditSeverity, AuditQuery

logger = logging.getLogger(__name__)


class AuditService:
    """
    Central service for audit trail management.
    Provides immutable, append-only audit logging with integrity checks.
    """
    
    def __init__(self, repository=None):
        """
        Initialize with optional repository for persistence.
        Repository is injected to allow different storage backends.
        """
        self.repository = repository
        self._last_checksum: Optional[str] = None
    
    def log(
        self,
        action: AuditAction,
        actor_id: int,
        actor_email: str,
        actor_role: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        correlation_id: Optional[str] = None,
        triggered_by: str = "user",
        actor_ip: Optional[str] = None,
        severity: AuditSeverity = None
    ) -> AuditEntry:
        """
        Create and persist an audit entry.
        Automatically chains to previous entry for integrity.
        """
        # Auto-determine severity if not provided
        if severity is None:
            severity = self._determine_severity(action)
        
        entry = AuditEntry(
            id=None,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            actor_ip=actor_ip,
            action=action,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            correlation_id=correlation_id,
            triggered_by=triggered_by,
            timestamp=datetime.utcnow(),
            previous_checksum=self._last_checksum
        )
        
        # Calculate checksum (done in __post_init__)
        self._last_checksum = entry.checksum
        
        # Persist if repository available
        if self.repository:
            self.repository.save(entry)
        
        # Log to standard logger as well
        logger.info(
            f"AUDIT: {entry.generate_summary()}",
            extra={
                "audit_action": action.value,
                "audit_resource": f"{resource_type}:{resource_id}",
                "audit_actor": actor_email,
                "correlation_id": correlation_id
            }
        )
        
        return entry
    
    def _determine_severity(self, action: AuditAction) -> AuditSeverity:
        """Determine severity based on action type"""
        critical_actions = [
            AuditAction.PERMISSION_CHANGED,
            AuditAction.USER_PASSWORD_CHANGED,
            AuditAction.SYSTEM_CONFIG_CHANGED,
        ]
        
        high_actions = [
            AuditAction.SHIFT_DELETED,
            AuditAction.EMPLOYEE_DEACTIVATED,
            AuditAction.LEAVE_REJECTED,
            AuditAction.AI_OPTIMIZATION_RUN,
        ]
        
        low_actions = [
            AuditAction.USER_LOGIN,
            AuditAction.USER_LOGOUT,
        ]
        
        if action in critical_actions:
            return AuditSeverity.CRITICAL
        elif action in high_actions:
            return AuditSeverity.HIGH
        elif action in low_actions:
            return AuditSeverity.LOW
        else:
            return AuditSeverity.MEDIUM
    
    # ============== Convenience Methods ==============
    
    def log_shift_created(
        self,
        shift_data: Dict[str, Any],
        actor_id: int,
        actor_email: str,
        actor_role: str,
        correlation_id: str = None
    ) -> AuditEntry:
        """Log shift creation"""
        return self.log(
            action=AuditAction.SHIFT_CREATED,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            resource_type="shift",
            resource_id=shift_data.get("id"),
            after_state=shift_data,
            correlation_id=correlation_id
        )
    
    def log_shift_updated(
        self,
        shift_id: int,
        before: Dict[str, Any],
        after: Dict[str, Any],
        actor_id: int,
        actor_email: str,
        actor_role: str,
        reason: str = None,
        correlation_id: str = None
    ) -> AuditEntry:
        """Log shift update with before/after comparison"""
        return self.log(
            action=AuditAction.SHIFT_UPDATED,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            resource_type="shift",
            resource_id=shift_id,
            before_state=before,
            after_state=after,
            reason=reason,
            correlation_id=correlation_id
        )
    
    def log_leave_decision(
        self,
        leave_id: int,
        decision: str,  # approved/rejected
        actor_id: int,
        actor_email: str,
        actor_role: str,
        reason: str,
        auto_decided: bool = False,
        correlation_id: str = None
    ) -> AuditEntry:
        """Log leave request decision"""
        action = AuditAction.LEAVE_APPROVED if decision == "approved" else AuditAction.LEAVE_REJECTED
        
        return self.log(
            action=action,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            resource_type="leave_request",
            resource_id=leave_id,
            reason=reason,
            triggered_by="automation" if auto_decided else "user",
            correlation_id=correlation_id
        )
    
    def log_ai_optimization(
        self,
        optimization_result: Dict[str, Any],
        actor_id: int,
        actor_email: str,
        correlation_id: str = None
    ) -> AuditEntry:
        """Log AI optimization run"""
        return self.log(
            action=AuditAction.AI_OPTIMIZATION_RUN,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role="system",
            resource_type="optimization",
            after_state=optimization_result,
            triggered_by="ai",
            correlation_id=correlation_id,
            severity=AuditSeverity.HIGH
        )
    
    def log_auto_rebalance(
        self,
        trigger_reason: str,
        affected_shifts: List[int],
        correlation_id: str = None
    ) -> AuditEntry:
        """Log automatic shift rebalancing"""
        return self.log(
            action=AuditAction.AUTO_REBALANCE_TRIGGERED,
            actor_id=0,
            actor_email="system@shiftmaster.ai",
            actor_role="system",
            resource_type="shift_rebalance",
            after_state={
                "trigger_reason": trigger_reason,
                "affected_shift_ids": affected_shifts
            },
            triggered_by="automation",
            correlation_id=correlation_id
        )
    
    def log_login(
        self,
        user_id: int,
        email: str,
        role: str,
        ip_address: str = None,
        user_agent: str = None,
        success: bool = True
    ) -> AuditEntry:
        """Log user login attempt"""
        return self.log(
            action=AuditAction.USER_LOGIN,
            actor_id=user_id,
            actor_email=email,
            actor_role=role,
            actor_ip=ip_address,
            actor_user_agent=user_agent,
            resource_type="auth",
            after_state={"success": success},
            severity=AuditSeverity.LOW if success else AuditSeverity.HIGH
        )
    
    # ============== Query Methods ==============
    
    def query(self, query: AuditQuery) -> List[AuditEntry]:
        """Query audit logs with filters"""
        if not self.repository:
            return []
        return self.repository.query(query)
    
    def get_resource_history(
        self,
        resource_type: str,
        resource_id: int,
        limit: int = 50
    ) -> List[AuditEntry]:
        """Get complete history for a specific resource"""
        query = AuditQuery(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit
        )
        return self.query(query)
    
    def get_user_activity(
        self,
        user_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Get all activity by a specific user"""
        query = AuditQuery(
            actor_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return self.query(query)
    
    def verify_chain_integrity(self, entries: List[AuditEntry]) -> Tuple[bool, List[str]]:
        """
        Verify the integrity of a chain of audit entries.
        Returns (is_valid, list of errors)
        """
        errors = []
        
        for i, entry in enumerate(entries):
            # Verify individual entry integrity
            if not entry.verify_integrity():
                errors.append(f"Entry {entry.id} checksum mismatch - possible tampering")
            
            # Verify chain continuity
            if i > 0:
                expected_prev = entries[i-1].checksum
                if entry.previous_checksum != expected_prev:
                    errors.append(f"Entry {entry.id} chain broken - expected {expected_prev}, got {entry.previous_checksum}")
        
        return len(errors) == 0, errors


# Type hint helper
from typing import Tuple
