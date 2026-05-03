"""
Tests for authentication, authorization, and role-based access control.
"""

from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
import json

User = get_user_model()


class UserRegistrationTestCase(APITestCase):
    """Test user registration endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('user-list')
    
    def test_user_registration_success(self):
        """Test successful user registration"""
        data = {
            'email': 'newuser@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'HR',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'newuser@example.com')
        self.assertEqual(response.data['role'], 'HR')
        
        # Verify user was created
        user = User.objects.get(email='newuser@example.com')
        self.assertIsNotNone(user)
        self.assertEqual(user.role, 'HR')
    
    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = {
            'email': 'newuser@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'DifferentPassword!',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'HR',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create first user
        User.objects.create_user(
            email='existing@example.com',
            password='TestPassword123!',
            role='HR'
        )
        
        # Try to register with same email
        data = {
            'email': 'existing@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'role': 'ACCOUNTANT',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_registration_invalid_role(self):
        """Test registration with invalid role"""
        data = {
            'email': 'newuser@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'INVALID_ROLE',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTestCase(APITestCase):
    """Test user login (JWT token) endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('token_obtain_pair')
        
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPassword123!',
            role='HR',
            first_name='Test',
            last_name='User'
        )
    
    def test_login_success(self):
        """Test successful login"""
        data = {
            'email': 'testuser@example.com',
            'password': 'TestPassword123!',
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify tokens are returned
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        
        # Verify user data
        self.assertEqual(response.data['user']['email'], 'testuser@example.com')
        self.assertEqual(response.data['user']['role'], 'HR')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'testuser@example.com',
            'password': 'WrongPassword!',
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_nonexistent_user(self):
        """Test login with nonexistent user"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123!',
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticationTestCase(APITestCase):
    """Test authentication requirement for protected endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPassword123!',
            role='HR'
        )
        
        # Get access token
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'testuser@example.com',
            'password': 'TestPassword123!',
        })
        self.access_token = response.data['access']
    
    def test_access_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = self.client.get(reverse('user-me'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_access_protected_endpoint_with_valid_token(self):
        """Test accessing protected endpoint with valid token"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(reverse('user-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'testuser@example.com')
    
    def test_access_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get(reverse('user-me'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileTestCase(APITestCase):
    """Test user profile endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPassword123!',
            role='HR',
            first_name='Test',
            last_name='User'
        )
        
        # Get access token
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'testuser@example.com',
            'password': 'TestPassword123!',
        })
        self.access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_get_user_profile(self):
        """Test getting current user profile"""
        response = self.client.get(reverse('user-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'testuser@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
        self.assertEqual(response.data['role'], 'HR')
    
    def test_update_user_profile(self):
        """Test updating user profile"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
        }
        response = self.client.patch(
            reverse('user-detail', args=[self.user.id]),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
    
    def test_change_password(self):
        """Test changing password"""
        data = {
            'old_password': 'TestPassword123!',
            'new_password': 'NewPassword456!',
            'new_password_confirm': 'NewPassword456!',
        }
        response = self.client.post(
            reverse('user-change-password'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword456!'))


class RoleBasedAccessTestCase(APITestCase):
    """Test role-based access control"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create users with different roles
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPassword123!',
            role='ADMIN'
        )
        
        self.hr_user = User.objects.create_user(
            email='hr@example.com',
            password='HRPassword123!',
            role='HR'
        )
        
        self.accountant_user = User.objects.create_user(
            email='accountant@example.com',
            password='AccountantPassword123!',
            role='ACCOUNTANT'
        )
    
    def test_admin_can_list_users(self):
        """Test that admin can list all users"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'admin@example.com',
            'password': 'AdminPassword123!',
        })
        token = response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_non_admin_cannot_list_users(self):
        """Test that non-admin users cannot list all users"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'hr@example.com',
            'password': 'HRPassword123!',
        })
        token = response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_user_can_update_own_profile(self):
        """Test that user can update their own profile"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'hr@example.com',
            'password': 'HRPassword123!',
        })
        token = response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {'first_name': 'Updated'}
        response = self.client.patch(
            reverse('user-detail', args=[self.hr_user.id]),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TokenRefreshTestCase(APITestCase):
    """Test JWT token refresh"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPassword123!',
            role='HR'
        )
        
        # Get tokens
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'testuser@example.com',
            'password': 'TestPassword123!',
        })
        self.refresh_token = response.data['refresh']
    
    def test_token_refresh(self):
        """Test refreshing access token"""
        response = self.client.post(reverse('token_refresh'), {
            'refresh': self.refresh_token,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_refresh_invalid_token(self):
        """Test refresh with invalid token"""
        response = self.client.post(reverse('token_refresh'), {
            'refresh': 'invalid_token',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DocumentUploadAuthenticationTestCase(APITestCase):
    """Test document upload requires authentication"""
    
    def setUp(self):
        self.client = APIClient()
        self.upload_url = reverse('upload_document')
        
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPassword123!',
            role='HR'
        )
        
        # Get access token
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'testuser@example.com',
            'password': 'TestPassword123!',
        })
        self.access_token = response.data['access']
    
    def test_document_upload_without_authentication(self):
        """Test document upload without token"""
        response = self.client.post(self.upload_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_document_upload_with_authentication(self):
        """Test document upload with valid token"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        file = SimpleUploadedFile(
            "test.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(
            self.upload_url,
            {'file': file},
            format='multipart'
        )
        # Should succeed (201 or 400 if file validation fails, but auth passes)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
