from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
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


@api_view(['POST'])
def login_view(request):
    """
    Login endpoint that returns JWT tokens and user data.
    
    POST /api/accounts/login/
    Body: {"email": "user@example.com", "password": "password"}
    Returns: {"access": "...", "refresh": "...", "user": {...}}
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'detail': 'Please provide email and password.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(request, username=email, password=password)
    
    if user is None:
        return Response(
            {'detail': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def register_view(request):
    """
    Register endpoint that creates a new user and returns JWT tokens.
    
    POST /api/accounts/register/
    Body: {
        "email": "user@example.com",
        "password": "password",
        "first_name": "John",
        "last_name": "Doe"
    }
    Returns: {"access": "...", "refresh": "...", "user": {...}}
    """
    data = request.data.copy()
    data.pop('role', None)
    serializer = UserCreateSerializer(data=data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def profile_view(request):
    """
    Get current user profile.
    
    GET /api/accounts/profile/
    Headers: Authorization: Bearer {token}
    Returns: User data
    """
    if not request.user.is_authenticated:
        return Response(
            {'detail': 'Not authenticated.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    serializer = UserSerializer(request.user)
    print(serializer.data)
    return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users (admin only).
    
    Endpoints:
    - GET /api/accounts/users/: Get all users (admin only)
    - POST /api/accounts/users/: Create a new user (admin only)
    - GET /api/accounts/users/{id}/: Get user details (admin)
    - PATCH /api/accounts/users/{id}/: Update user (admin)
    - DELETE /api/accounts/users/{id}/: Delete user (admin only)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action"""
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def perform_update(self, serializer):
        """Update user"""
        serializer.save()
