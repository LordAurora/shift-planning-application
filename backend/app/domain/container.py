"""
Service container for dependency injection of domain services.

This module provides a centralized container for all domain services,
making it easy to inject them into FastAPI routes.
"""

from functools import lru_cache
from typing import Optional
from sqlalchemy.orm import Session

from ..database import get_db
from .services.rule_engine import RuleEngine
from .services.shift_optimization_service import ShiftOptimizationService, OptimizationStrategy
from .services.leave_service import LeaveProcessingService
from .services.audit_service import AuditService
from .services.permission_service import PermissionService


class ServiceContainer:
    """
    Container for domain services with lazy initialization.
    
    Usage:
        container = ServiceContainer()
        rule_engine = container.rule_engine
        
    Or with FastAPI dependency:
        def get_services() -> ServiceContainer:
            return ServiceContainer()
    """
    
    _rule_engine: Optional[RuleEngine] = None
    _permission_service: Optional[PermissionService] = None
    _audit_service: Optional[AuditService] = None
    _shift_service: Optional[ShiftOptimizationService] = None
    _leave_service: Optional[LeaveProcessingService] = None
    
    def __init__(self, db: Optional[Session] = None):
        self._db = db
    
    @property
    def rule_engine(self) -> RuleEngine:
        """Get or create rule engine instance."""
        if self._rule_engine is None:
            self._rule_engine = RuleEngine()
        return self._rule_engine
    
    @property
    def permission_service(self) -> PermissionService:
        """Get or create permission service instance."""
        if self._permission_service is None:
            self._permission_service = PermissionService()
        return self._permission_service
    
    @property
    def audit_service(self) -> AuditService:
        """Get or create audit service instance."""
        if self._audit_service is None:
            self._audit_service = AuditService()
        return self._audit_service
    
    @property
    def shift_service(self) -> ShiftOptimizationService:
        """Get or create shift optimization service instance."""
        if self._shift_service is None:
            self._shift_service = ShiftOptimizationService(
                rule_engine=self.rule_engine
            )
        return self._shift_service
    
    @property
    def leave_service(self) -> LeaveProcessingService:
        """Get or create leave processing service instance."""
        if self._leave_service is None:
            self._leave_service = LeaveProcessingService(
                rule_engine=self.rule_engine,
                audit_service=self.audit_service
            )
        return self._leave_service


# Global singleton instance (for non-request contexts like Celery tasks)
_global_container: Optional[ServiceContainer] = None


def get_global_container() -> ServiceContainer:
    """Get global service container for non-request contexts."""
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer()
    return _global_container


# FastAPI dependency
def get_services() -> ServiceContainer:
    """
    FastAPI dependency for service container.
    
    Usage in routes:
        @router.get("/shifts")
        def get_shifts(services: ServiceContainer = Depends(get_services)):
            return services.shift_service.get_recommendations(...)
    """
    return ServiceContainer()


def get_rule_engine() -> RuleEngine:
    """FastAPI dependency for rule engine."""
    return get_services().rule_engine


def get_permission_service() -> PermissionService:
    """FastAPI dependency for permission service."""
    return get_services().permission_service


def get_audit_service() -> AuditService:
    """FastAPI dependency for audit service."""
    return get_services().audit_service


def get_shift_service() -> ShiftOptimizationService:
    """FastAPI dependency for shift optimization service."""
    return get_services().shift_service


def get_leave_service() -> LeaveProcessingService:
    """FastAPI dependency for leave processing service."""
    return get_services().leave_service
