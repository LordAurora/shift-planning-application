"""
Domain layer for shift planning application.

This package contains pure business logic separated from infrastructure:
- Domain models (entities, value objects)
- Domain services (business rules, orchestration)
- Service container (dependency injection)
"""

from .container import (
    ServiceContainer,
    get_services,
    get_rule_engine,
    get_permission_service,
    get_audit_service,
    get_shift_service,
    get_leave_service,
    get_global_container
)

__all__ = [
    'ServiceContainer',
    'get_services',
    'get_rule_engine',
    'get_permission_service',
    'get_audit_service',
    'get_shift_service',
    'get_leave_service',
    'get_global_container'
]
