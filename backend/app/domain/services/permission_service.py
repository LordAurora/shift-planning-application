"""
Permission Service - Central RBAC and permission matrix.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set
from functools import lru_cache


class Permission(str, Enum):
    """All system permissions"""
    # Shift Management
    SHIFT_VIEW_OWN = "shift:view:own"
    SHIFT_VIEW_TEAM = "shift:view:team"
    SHIFT_VIEW_ALL = "shift:view:all"
    SHIFT_CREATE = "shift:create"
    SHIFT_UPDATE_OWN = "shift:update:own"
    SHIFT_UPDATE_ALL = "shift:update:all"
    SHIFT_DELETE = "shift:delete"
    SHIFT_APPROVE = "shift:approve"
    SHIFT_SWAP_REQUEST = "shift:swap:request"
    SHIFT_SWAP_APPROVE = "shift:swap:approve"
    
    # Employee Management
    EMPLOYEE_VIEW_OWN = "employee:view:own"
    EMPLOYEE_VIEW_TEAM = "employee:view:team"
    EMPLOYEE_VIEW_ALL = "employee:view:all"
    EMPLOYEE_CREATE = "employee:create"
    EMPLOYEE_UPDATE = "employee:update"
    EMPLOYEE_DELETE = "employee:delete"
    EMPLOYEE_DEACTIVATE = "employee:deactivate"
    
    # Leave Management
    LEAVE_VIEW_OWN = "leave:view:own"
    LEAVE_VIEW_TEAM = "leave:view:team"
    LEAVE_VIEW_ALL = "leave:view:all"
    LEAVE_REQUEST = "leave:request"
    LEAVE_CANCEL_OWN = "leave:cancel:own"
    LEAVE_APPROVE = "leave:approve"
    LEAVE_REJECT = "leave:reject"
    
    # Department Management
    DEPARTMENT_VIEW = "department:view"
    DEPARTMENT_CREATE = "department:create"
    DEPARTMENT_UPDATE = "department:update"
    DEPARTMENT_DELETE = "department:delete"
    
    # Rules & AI
    RULE_VIEW = "rule:view"
    RULE_CREATE = "rule:create"
    RULE_UPDATE = "rule:update"
    RULE_DELETE = "rule:delete"
    AI_OPTIMIZATION_RUN = "ai:optimization:run"
    AI_OPTIMIZATION_APPROVE = "ai:optimization:approve"
    AI_SETTINGS = "ai:settings"
    
    # Reports & Analytics
    REPORT_VIEW_OWN = "report:view:own"
    REPORT_VIEW_TEAM = "report:view:team"
    REPORT_VIEW_ALL = "report:view:all"
    ANALYTICS_VIEW = "analytics:view"
    AUDIT_LOG_VIEW = "audit:view"
    
    # System Administration
    USER_MANAGE = "user:manage"
    ROLE_MANAGE = "role:manage"
    SYSTEM_CONFIG = "system:config"
    NOTIFICATION_SEND = "notification:send"
    BACKUP_MANAGE = "backup:manage"


class Role(str, Enum):
    """System roles"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    EMPLOYEE = "employee"


@dataclass
class ResourceContext:
    """Context for permission checks"""
    resource_type: str
    resource_id: Optional[int] = None
    owner_id: Optional[int] = None
    department_id: Optional[int] = None
    team_ids: Optional[List[int]] = None


@dataclass
class UserContext:
    """User context for permission checks"""
    user_id: int
    role: Role
    department_id: Optional[int] = None
    managed_team_ids: Optional[List[int]] = None
    custom_permissions: Optional[Set[Permission]] = None
    denied_permissions: Optional[Set[Permission]] = None


# ============== Permission Matrix ==============

ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),  # All permissions
    
    Role.ADMIN: {
        # Shifts
        Permission.SHIFT_VIEW_ALL,
        Permission.SHIFT_CREATE,
        Permission.SHIFT_UPDATE_ALL,
        Permission.SHIFT_DELETE,
        Permission.SHIFT_APPROVE,
        Permission.SHIFT_SWAP_APPROVE,
        # Employees
        Permission.EMPLOYEE_VIEW_ALL,
        Permission.EMPLOYEE_CREATE,
        Permission.EMPLOYEE_UPDATE,
        Permission.EMPLOYEE_DEACTIVATE,
        # Leave
        Permission.LEAVE_VIEW_ALL,
        Permission.LEAVE_APPROVE,
        Permission.LEAVE_REJECT,
        # Departments
        Permission.DEPARTMENT_VIEW,
        Permission.DEPARTMENT_CREATE,
        Permission.DEPARTMENT_UPDATE,
        # Rules & AI
        Permission.RULE_VIEW,
        Permission.RULE_CREATE,
        Permission.RULE_UPDATE,
        Permission.AI_OPTIMIZATION_RUN,
        Permission.AI_OPTIMIZATION_APPROVE,
        # Reports
        Permission.REPORT_VIEW_ALL,
        Permission.ANALYTICS_VIEW,
        Permission.AUDIT_LOG_VIEW,
        # System
        Permission.USER_MANAGE,
        Permission.NOTIFICATION_SEND,
    },
    
    Role.MANAGER: {
        # Shifts
        Permission.SHIFT_VIEW_TEAM,
        Permission.SHIFT_CREATE,
        Permission.SHIFT_UPDATE_ALL,
        Permission.SHIFT_APPROVE,
        Permission.SHIFT_SWAP_APPROVE,
        # Employees
        Permission.EMPLOYEE_VIEW_TEAM,
        Permission.EMPLOYEE_CREATE,
        Permission.EMPLOYEE_UPDATE,
        # Leave
        Permission.LEAVE_VIEW_TEAM,
        Permission.LEAVE_APPROVE,
        Permission.LEAVE_REJECT,
        # Departments
        Permission.DEPARTMENT_VIEW,
        # Rules & AI
        Permission.RULE_VIEW,
        Permission.AI_OPTIMIZATION_RUN,
        # Reports
        Permission.REPORT_VIEW_TEAM,
        Permission.ANALYTICS_VIEW,
    },
    
    Role.SUPERVISOR: {
        # Shifts
        Permission.SHIFT_VIEW_TEAM,
        Permission.SHIFT_SWAP_APPROVE,
        # Employees
        Permission.EMPLOYEE_VIEW_TEAM,
        # Leave
        Permission.LEAVE_VIEW_TEAM,
        # Departments
        Permission.DEPARTMENT_VIEW,
        # Rules
        Permission.RULE_VIEW,
        # Reports
        Permission.REPORT_VIEW_TEAM,
    },
    
    Role.EMPLOYEE: {
        # Shifts
        Permission.SHIFT_VIEW_OWN,
        Permission.SHIFT_SWAP_REQUEST,
        # Employees
        Permission.EMPLOYEE_VIEW_OWN,
        # Leave
        Permission.LEAVE_VIEW_OWN,
        Permission.LEAVE_REQUEST,
        Permission.LEAVE_CANCEL_OWN,
        # Reports
        Permission.REPORT_VIEW_OWN,
    },
}


class PermissionService:
    """
    Central permission resolution service.
    Handles role-based and attribute-based access control.
    """
    
    def __init__(self):
        self._permission_cache: Dict[str, bool] = {}
    
    @lru_cache(maxsize=1000)
    def get_role_permissions(self, role: Role) -> frozenset:
        """Get all permissions for a role"""
        return frozenset(ROLE_PERMISSIONS.get(role, set()))
    
    def has_permission(
        self,
        user: UserContext,
        permission: Permission,
        resource: Optional[ResourceContext] = None
    ) -> bool:
        """
        Check if user has permission, optionally considering resource context.
        """
        # Super admin bypass
        if user.role == Role.SUPER_ADMIN:
            return True
        
        # Check denied permissions first (explicit denials)
        if user.denied_permissions and permission in user.denied_permissions:
            return False
        
        # Check custom permissions (explicit grants)
        if user.custom_permissions and permission in user.custom_permissions:
            return True
        
        # Check role-based permissions
        role_perms = self.get_role_permissions(user.role)
        if permission not in role_perms:
            return False
        
        # If no resource context, permission is granted based on role
        if resource is None:
            return True
        
        # Attribute-based access control
        return self._check_abac(user, permission, resource)
    
    def _check_abac(
        self,
        user: UserContext,
        permission: Permission,
        resource: ResourceContext
    ) -> bool:
        """Attribute-based access control checks"""
        
        # Own-resource permissions
        if ":own" in permission.value:
            if resource.owner_id is None:
                return False
            return resource.owner_id == user.user_id
        
        # Team-resource permissions
        if ":team" in permission.value:
            if user.managed_team_ids is None or resource.team_ids is None:
                return False
            return bool(set(user.managed_team_ids) & set(resource.team_ids))
        
        # Department-based permissions (if same department)
        if user.department_id and resource.department_id:
            if user.department_id == resource.department_id:
                return True
        
        # All-resource permissions already handled by role check
        return True
    
    def get_user_permissions(self, user: UserContext) -> Set[Permission]:
        """Get all effective permissions for a user"""
        if user.role == Role.SUPER_ADMIN:
            return set(Permission)
        
        # Start with role permissions
        permissions = set(ROLE_PERMISSIONS.get(user.role, set()))
        
        # Add custom permissions
        if user.custom_permissions:
            permissions.update(user.custom_permissions)
        
        # Remove denied permissions
        if user.denied_permissions:
            permissions -= user.denied_permissions
        
        return permissions
    
    def filter_accessible_resources(
        self,
        user: UserContext,
        resources: List[ResourceContext],
        permission: Permission
    ) -> List[ResourceContext]:
        """Filter resources to only those user can access"""
        return [
            r for r in resources
            if self.has_permission(user, permission, r)
        ]
    
    def can_manage_employee(
        self,
        user: UserContext,
        employee_id: int,
        employee_department_id: Optional[int] = None
    ) -> bool:
        """Check if user can manage a specific employee"""
        if user.role in [Role.SUPER_ADMIN, Role.ADMIN]:
            return True
        
        if user.role == Role.MANAGER:
            # Managers can manage employees in their department
            if user.department_id and user.department_id == employee_department_id:
                return True
            # Or in their managed teams
            if user.managed_team_ids:
                # Would need employee team info here
                return True
        
        return False
    
    def can_approve_leave(
        self,
        user: UserContext,
        requester_id: int,
        requester_department_id: Optional[int] = None
    ) -> bool:
        """Check if user can approve leave for another user"""
        # Cannot approve own leave
        if user.user_id == requester_id:
            return False
        
        return self.has_permission(
            user,
            Permission.LEAVE_APPROVE,
            ResourceContext(
                resource_type="leave",
                owner_id=requester_id,
                department_id=requester_department_id
            )
        )
    
    def get_data_scope(self, user: UserContext, resource_type: str) -> str:
        """
        Determine data scope for a user viewing a resource type.
        Returns: 'all', 'team', 'department', 'own'
        """
        if user.role == Role.SUPER_ADMIN:
            return "all"
        
        # Check in order of broadest to narrowest
        all_perm = Permission(f"{resource_type}:view:all")
        team_perm = Permission(f"{resource_type}:view:team")
        own_perm = Permission(f"{resource_type}:view:own")
        
        if self.has_permission(user, all_perm):
            return "all"
        elif self.has_permission(user, team_perm):
            return "team"
        elif self.has_permission(user, own_perm):
            return "own"
        
        return "none"


# Singleton instance
permission_service = PermissionService()


def require_permission(permission: Permission):
    """
    Decorator for FastAPI endpoints to require a permission.
    Usage: @require_permission(Permission.SHIFT_CREATE)
    """
    def decorator(func):
        async def wrapper(*args, current_user=None, **kwargs):
            if current_user is None:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_context = UserContext(
                user_id=current_user.id,
                role=Role(current_user.role),
                department_id=getattr(current_user, 'department_id', None)
            )
            
            if not permission_service.has_permission(user_context, permission):
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value}"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
