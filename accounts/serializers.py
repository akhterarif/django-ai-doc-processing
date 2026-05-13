from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

from .models import UserRole

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with user data.
    
    Returns: {
        "access": "...",
        "refresh": "...",
        "user": {
            "id": 1,
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "is_staff": true,
            "is_active": true,
            "role": "ADMIN"
        }
    }
    """
    username_field = 'email'
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims to token
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        token['role'] = user.role
        return token
    
    def validate(self, attrs):
        """Override validate to include user data in response"""
        data = super().validate(attrs)
        
        # Add user data to response
        user = self.user
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'role': user.role,
        }
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """User serializer for reading user data"""
    date_joined = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """User serializer for creating new users (registration and admin creation)"""
    
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=UserRole.choices, default=UserRole.HR, required=False)
    date_joined = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
        read_only_fields = ['id', 'is_active', 'date_joined']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.get('role', UserRole.HR)
        validated_data['is_staff'] = role == UserRole.ADMIN
        user = User.objects.create_user(**validated_data, password=password)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """User serializer for updating user data"""

    role = serializers.ChoiceField(choices=UserRole.choices)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'role']

    def update(self, instance, validated_data):
        if 'role' in validated_data:
            instance.is_staff = validated_data['role'] == UserRole.ADMIN
        return super().update(instance, validated_data)
    """User serializer for updating user data"""
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_staff']
