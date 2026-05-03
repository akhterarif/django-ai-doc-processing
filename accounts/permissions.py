from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsAdmin(permissions.BasePermission):
    """Permission to check if user is admin"""
    message = 'Only admins can access this resource.'
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')


class IsHR(permissions.BasePermission):
    """Permission to check if user is HR"""
    message = 'Only HR users can access this resource.'
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'HR')


class IsAccountant(permissions.BasePermission):
    """Permission to check if user is accountant"""
    message = 'Only accountants can access this resource.'
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ACCOUNTANT')


class IsLegal(permissions.BasePermission):
    """Permission to check if user is legal"""
    message = 'Only legal users can access this resource.'
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'LEGAL')


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permission to allow admin full access, others read-only"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')


class HasRolePermission(permissions.BasePermission):
    """
    Base permission class for role-based access control.
    Override role_required_methods in the view to specify required roles.
    """
    
    def has_permission(self, request, view):
        # Allow unauthenticated users for specific endpoints (handled by view)
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if view has role requirements
        role_required_methods = getattr(view, 'role_required_methods', {})
        method = request.method.upper()
        
        if method not in role_required_methods:
            return True
        
        required_roles = role_required_methods[method]
        user_role = getattr(request.user, 'role', None)
        
        return user_role in required_roles
