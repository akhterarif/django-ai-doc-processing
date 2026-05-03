from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view (login endpoint).
    
    POST /api/accounts/auth/token/
    Body: {"email": "user@example.com", "password": "password"}
    Returns: {"access": "...", "refresh": "...", "user": {...}}
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    
    Endpoints:
    - POST /api/accounts/users/ (register): Create a new user (public)
    - GET /api/accounts/users/ (list): Get all users (admin only)
    - GET /api/accounts/users/{id}/ (retrieve): Get user details (self or admin)
    - PATCH /api/accounts/users/{id}/ (partial_update): Update user (self or admin)
    - DELETE /api/accounts/users/{id}/ (destroy): Delete user (admin only)
    - GET /api/accounts/users/me/ (me): Get current user profile (authenticated)
    - POST /api/accounts/users/change_password/ (change_password): Change user password (authenticated)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """Set permission classes based on action"""
        if self.action == 'create':
            # Registration is public
            permission_classes = [AllowAny]
        elif self.action in ['list', 'destroy']:
            # Only admins can list or delete users
            permission_classes = [IsAdminUser]
        elif self.action == 'me':
            # Must be authenticated to get own profile
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update']:
            # Must be authenticated; can update own profile or be admin
            permission_classes = [IsAuthenticated]
        else:
            # Default to authenticated
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def perform_update(self, serializer):
        """Update user - ensure users can only update their own profile unless admin"""
        user = self.request.user
        target_user = self.get_object()
        if user.id != target_user.id and not user.is_staff:
            raise PermissionError('You can only update your own profile.')
        serializer.save()
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current user profile.
        
        GET /api/accounts/users/me/
        Returns: Current user data
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change user password.
        
        POST /api/accounts/users/change_password/
        Body: {
            "old_password": "old_password",
            "new_password": "new_password",
            "new_password_confirm": "new_password"
        }
        """
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')
        
        if not old_password or not new_password or not new_password_confirm:
            return Response(
                {'detail': 'Please provide old_password, new_password, and new_password_confirm.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(old_password):
            return Response(
                {'detail': 'Old password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password != new_password_confirm:
            return Response(
                {'detail': 'New passwords do not match.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)
