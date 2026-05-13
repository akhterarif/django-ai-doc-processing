# Implementation Guide: Authentication & Authorization

## Overview

This guide provides a complete overview of how authentication and role-based authorization are implemented in this Django REST API.

---

## Architecture

### Components

1. **CustomUser Model** (`accounts/models.py`)
   - Email-based authentication (not username)
   - Role field with choices: ADMIN, HR, ACCOUNTANT, LEGAL
   - Timestamps for audit trails

2. **JWT Authentication** (`rest_framework_simplejwt`)
   - Access token (60-minute lifetime)
   - Refresh token (7-day lifetime)
   - Token rotation and blacklisting enabled

3. **Permissions** (`accounts/permissions.py`)
   - Role-based permission classes
   - IsAdmin, IsHR, IsAccountant, IsLegal
   - HasRolePermission for flexible role checking

4. **Middleware** (`accounts/middleware.py`)
   - AuthLoggingMiddleware: Logs all requests with user info
   - RoleBasedAccessMiddleware: Enforces role-based access at middleware level

5. **Views** (`accounts/views.py`)
   - CustomTokenObtainPairView: Login endpoint
   - UserViewSet: User management CRUD

---

## Request Flow

### 1. User Registration

```
POST /api/accounts/users/
{
  "email": "user@example.com",
  "password": "password123",
  "password_confirm": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "HR"
}
↓
UserCreateSerializer validates input
↓
CustomUserManager.create_user() creates user
↓
201 CREATED response with user data
```

### 2. User Login

```
POST /api/accounts/auth/token/
{
  "email": "user@example.com",
  "password": "password123"
}
↓
CustomTokenObtainPairSerializer validates credentials
↓
get_token() generates JWT with claims (email, role)
↓
200 OK response with:
- access token
- refresh token
- user data
```

### 3. Protected Request

```
GET /api/accounts/users/me/
Header: Authorization: Bearer {access_token}
↓
JWTAuthentication extracts and validates token
↓
IsAuthenticated permission check
↓
View processes request with authenticated user
↓
200 OK with user data
```

### 4. Token Refresh

```
POST /api/accounts/auth/token/refresh/
{
  "refresh": {refresh_token}
}
↓
TokenRefreshView validates refresh token
↓
New access token generated
↓
Old refresh token blacklisted (rotate=True)
↓
200 OK with new access token
```

---

## Permission Classes

### Role-Based Permission Classes

Located in `accounts/permissions.py`:

```python
# Example: Admin-only endpoint
from accounts.permissions import IsAdmin

class AdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
```

Available classes:
- `IsAdmin`: Only ADMIN role
- `IsHR`: Only HR role
- `IsAccountant`: Only ACCOUNTANT role
- `IsLegal`: Only LEGAL role
- `IsAdminOrReadOnly`: ADMIN has full access, others read-only
- `HasRolePermission`: Flexible role checking

### Usage Examples

```python
# Single role requirement
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsAdmin

@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_only_view(request):
    return Response({'message': 'Admin only'})


# Multiple permission classes
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsHR

class HRView(APIView):
    permission_classes = [IsAuthenticated, IsHR]
```

---

## Middleware

### AuthLoggingMiddleware

Logs all incoming and outgoing requests with user information.

**Log Format:**
```
INFO: Request: POST /api/documents/upload
extra={'user': 'user@example.com', 'role': 'HR', 'ip': '127.0.0.1', 'user_agent': '...'}

INFO: Response: POST /api/documents/upload - 201
extra={'user': 'user@example.com', 'role': 'HR', 'status_code': 201}
```

**Configuration:** No configuration needed, automatically enabled.

### RoleBasedAccessMiddleware

Provides role-based access control at the middleware level.

**Configuration** (optional, in `settings.py`):

```python
ROLE_BASED_ACCESS_RULES = {
    '/api/admin/': ['ADMIN'],
    '/api/accounts/users/': ['ADMIN'],
    '/api/documents/': ['HR', 'ACCOUNTANT', 'LEGAL'],
}
```

**Response on access denied:**
```json
{
  "detail": "User with role HR cannot access this resource. Required roles: ADMIN"
}
```

---

## Settings Configuration

### Installed Apps

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework_simplejwt',
    'accounts',
    'documents',
    'ai',
    'workflows',
]
```

### Middleware

```python
MIDDLEWARE = [
    # ...
    'accounts.middleware.AuthLoggingMiddleware',
    'accounts.middleware.RoleBasedAccessMiddleware',
]
```

### REST Framework Configuration

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}
```

### JWT Configuration

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.getenv('SECRET_KEY', SECRET_KEY),
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### Custom User Model

```python
AUTH_USER_MODEL = 'accounts.CustomUser'
```

---

## Document Upload Authorization

### Current Implementation

Document upload endpoint requires authentication:

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document(request):
    # document automatically associated with request.user
    document = serializer.save(user=request.user)
```

### Query Filtering

Users only see their own documents:

```python
def list_documents(request):
    docs = Document.objects.filter(user=request.user)
```

### Future Role-Based Enhancement

To restrict uploads by role:

```python
from accounts.permissions import IsHR, IsAccountant, IsLegal

@api_view(['POST'])
@permission_classes([IsHR | IsAccountant | IsLegal])
def upload_document(request):
    # Only HR, Accountant, or Legal can upload
```

Or using permission classes:

```python
class MultiRolePermission(BasePermission):
    def has_permission(self, request, view):
        allowed_roles = ['HR', 'ACCOUNTANT', 'LEGAL']
        return request.user.role in allowed_roles
```

---

## Common Patterns

### Admin-Only View

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard(request):
    return Response({'data': 'admin data'})
```

### Role-Restricted ViewSet

```python
from rest_framework import viewsets
from accounts.permissions import IsHR

class HRDocumentsViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsHR]
    
    def get_queryset(self):
        # HR users see all documents, others see only their own
        user = self.request.user
        if user.role == 'HR':
            return Document.objects.all()
        return Document.objects.filter(user=user)
```

### Conditional Permissions

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser

@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def document_detail(request, pk):
    document = Document.objects.get(pk=pk)
    
    # Check authorization
    if request.method == 'DELETE':
        if request.user != document.user and not request.user.is_staff:
            return Response(
                {'detail': 'Cannot delete document you do not own'},
                status=403
            )
    
    return Response({'data': 'document data'})
```

### Multiple Role Check

```python
from accounts.permissions import BasePermission

class IsHROrAccountant(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['HR', 'ACCOUNTANT']

class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsHROrAccountant]
```

---

## Testing

### Running Tests

```bash
# All tests
python manage.py test accounts

# Specific test class
python manage.py test accounts.tests.UserRegistrationTestCase

# With verbosity
python manage.py test accounts --verbosity=2

# With coverage
coverage run --source='accounts' manage.py test accounts
coverage report
```

### Test Coverage

The test suite includes:

1. **User Registration Tests**
   - Successful registration
   - Password mismatch
   - Duplicate email
   - Invalid role

2. **Login Tests**
   - Successful login
   - Invalid credentials
   - Nonexistent user

3. **Authentication Tests**
   - Access without token
   - Access with valid token
   - Access with invalid token

4. **Profile Tests**
   - Get current user
   - Update profile
   - Change password

5. **Role-Based Access Tests**
   - Admin access
   - Non-admin access denied
   - Self profile update

6. **Token Tests**
   - Token refresh
   - Invalid refresh token

7. **Document Upload Tests**
   - Upload without auth
   - Upload with auth

---

## Troubleshooting

### Common Issues

#### "Authentication credentials were not provided"
- Missing Authorization header
- Token not included or malformed
- Check header format: `Authorization: Bearer {token}`

#### "Invalid token"
- Token expired (get new one using refresh)
- Token modified
- Wrong secret key (check SECRET_KEY in settings)

#### "Permission denied"
- User role not in allowed roles
- Not authenticated
- Admin-only endpoint accessed by non-admin

#### "Given token not valid for any token type"
- Token is invalid or corrupted
- Token from different token type
- Wrong token (access vs refresh)

### Debug Headers

```python
# In settings.py for development
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # For debugging
    ),
}
```

### Logging Configuration

```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

---

## Security Considerations

### Production Checklist

- [ ] Update `SECRET_KEY` via environment variable
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use HTTPS only
- [ ] Set secure cookie flags
- [ ] Implement CORS properly (not `CORS_ALLOW_ALL_ORIGINS`)
- [ ] Set strong password validation
- [ ] Enable token expiration
- [ ] Implement rate limiting
- [ ] Use environment variables for all secrets

### CORS Configuration

```python
# Correct (production)
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]

# Avoid in production
CORS_ALLOW_ALL_ORIGINS = True  # ❌ SECURITY RISK
```

### Rate Limiting

```python
# Install djangorestframework-ratelimit
pip install djangorestframework-ratelimit

# In settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

---

## API Endpoints Summary

### Authentication Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/api/accounts/users/` | No | Register new user |
| POST | `/api/accounts/auth/token/` | No | Login (get JWT tokens) |
| POST | `/api/accounts/auth/token/refresh/` | No | Refresh access token |

### User Management Endpoints

| Method | Endpoint | Auth Required | Permission |
|--------|----------|---------------|-----------|
| GET | `/api/accounts/users/` | Yes | Admin only |
| GET | `/api/accounts/users/me/` | Yes | Authenticated |
| GET | `/api/accounts/users/{id}/` | Yes | Self or Admin |
| PATCH | `/api/accounts/users/{id}/` | Yes | Self or Admin |
| DELETE | `/api/accounts/users/{id}/` | Yes | Admin only |
| POST | `/api/accounts/users/change_password/` | Yes | Authenticated |

### Document Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/api/documents/upload` | Yes | Upload document |
| GET | `/api/documents/` | Yes | List user's documents |
| GET | `/api/documents/{id}/` | Yes | Get document details |
| GET | `/api/documents/{id}/status/` | Yes | Get processing status |
