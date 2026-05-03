"""
Custom middleware for authentication and authorization.
Provides role-based request filtering and logging.
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class AuthLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log authentication events and track user activity.
    """
    
    def process_request(self, request):
        """Log incoming requests with user information"""
        user_info = "Anonymous"
        user_role = "N/A"
        
        if request.user and request.user.is_authenticated:
            user_info = request.user.email
            user_role = getattr(request.user, 'role', 'N/A')
        
        logger.info(
            f"Request: {request.method} {request.path}",
            extra={
                'user': user_info,
                'role': user_role,
                'ip': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'N/A'),
            }
        )
        return None
    
    def process_response(self, request, response):
        """Log response status"""
        user_info = "Anonymous"
        user_role = "N/A"
        
        if request.user and request.user.is_authenticated:
            user_info = request.user.email
            user_role = getattr(request.user, 'role', 'N/A')
        
        logger.info(
            f"Response: {request.method} {request.path} - {response.status_code}",
            extra={
                'user': user_info,
                'role': user_role,
                'status_code': response.status_code,
            }
        )
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RoleBasedAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce role-based access control at the middleware level.
    Provides an additional layer of security beyond DRF permissions.
    
    Configuration:
    ROLE_BASED_ACCESS_RULES = {
        '/api/admin-only/': ['ADMIN'],
        '/api/accounts/users/': ['ADMIN', 'HR'],
    }
    """
    
    def process_request(self, request):
        """Check if user has required role for the requested path"""
        from django.conf import settings
        
        rules = getattr(settings, 'ROLE_BASED_ACCESS_RULES', {})
        
        if not rules:
            return None
        
        # Check if the requested path matches any rule
        for path_pattern, allowed_roles in rules.items():
            if request.path.startswith(path_pattern):
                # If user is not authenticated, let DRF handle it
                if not request.user or not request.user.is_authenticated:
                    return None
                
                user_role = getattr(request.user, 'role', None)
                
                # Check if user's role is in allowed roles
                if user_role not in allowed_roles:
                    logger.warning(
                        f"Access denied: User {request.user.email} with role {user_role} "
                        f"tried to access {request.path}",
                        extra={'user': request.user.email, 'role': user_role}
                    )
                    return JsonResponse(
                        {
                            'detail': f'User with role {user_role} cannot access this resource. '
                                     f'Required roles: {", ".join(allowed_roles)}'
                        },
                        status=403
                    )
        
        return None
