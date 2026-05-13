# Quick Setup Guide: Authentication & Authorization

## What's Been Implemented

✅ **User Management**
- Custom user model with email-based login
- User roles: ADMIN, HR, ACCOUNTANT, LEGAL
- Password hashing with Django's built-in validators

✅ **JWT Authentication**
- Token-based authentication via `rest_framework_simplejwt`
- Access tokens (60-minute lifetime)
- Refresh tokens (7-day lifetime)
- Token rotation and automatic blacklisting

✅ **User Endpoints**
- Registration: `POST /api/accounts/users/`
- Login: `POST /api/accounts/auth/token/`
- Token refresh: `POST /api/accounts/auth/token/refresh/`
- Profile: `GET /api/accounts/users/me/`
- Update profile: `PATCH /api/accounts/users/{id}/`
- Change password: `POST /api/accounts/users/change_password/`
- List users (admin): `GET /api/accounts/users/`

✅ **Document Security**
- Document upload requires authentication: `POST /api/documents/upload`
- Users see only their own documents
- Document ownership tracked via user foreign key

✅ **Role-Based Permissions**
- Permission classes: `IsAdmin`, `IsHR`, `IsAccountant`, `IsLegal`
- Middleware for additional access control
- Flexible role-based permission system

✅ **Middleware & Logging**
- `AuthLoggingMiddleware`: Logs all requests with user info
- `RoleBasedAccessMiddleware`: Enforces role-based access rules
- Request/response logging for audit trails

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python manage.py makemigrations accounts documents workflows ai
python manage.py migrate
```

### 3. Create Superuser

```bash
python manage.py createsuperuser
# Email: admin@example.com
# Password: your-secure-password
# Role: Will be set to ADMIN automatically
```

### 4. Start Development Server

```bash
python manage.py runserver
```

### 5. Test API

**Register a new user:**
```bash
curl -X POST http://localhost:8000/api/accounts/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe",
    "role": "HR"
  }'
```

**Login (get tokens):**
```bash
curl -X POST http://localhost:8000/api/accounts/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 2,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "HR",
    "is_active": true
  }
}
```

**Get user profile:**
```bash
curl -X GET http://localhost:8000/api/accounts/users/me/ \
  -H "Authorization: Bearer {access_token}"
```

**Upload document:**
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer {access_token}" \
  -F "file=@document.pdf"
```

---

## API Documentation

See detailed documentation in:
- **[API_AUTHENTICATION.md](API_AUTHENTICATION.md)** - Complete API reference
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Technical implementation details

---

## File Structure

```
accounts/
├── __init__.py
├── models.py                    # CustomUser model with roles
├── serializers.py               # JWT and user serializers
├── views.py                     # Authentication views
├── permissions.py               # Role-based permission classes
├── middleware.py                # Auth logging & RBAC middleware
├── urls.py                      # Authentication endpoints
├── admin.py                     # Django admin configuration
├── migrations/                  # Database migrations
└── tests.py                     # Comprehensive test suite

documents/
├── models.py                    # Document model with user FK
├── views.py                     # Updated to require auth
├── serializers.py               # Updated with user field
└── ... (other files)

django_ai_doc_processing/
├── settings.py                  # JWT & middleware config
├── urls.py                      # Root URL patterns
└── ... (other files)
```

---

## Role Descriptions

### ADMIN
- Full system access
- Manage all users
- View all documents
- Access admin endpoints

### HR
- HR department access
- View/upload HR documents
- Standard user operations

### ACCOUNTANT
- Financial document access
- View/upload accounting documents
- Standard user operations

### LEGAL
- Legal document access
- View/upload legal documents
- Standard user operations

---

## Database Models

### CustomUser
```python
- email (unique, indexed)
- first_name
- last_name
- role (ADMIN, HR, ACCOUNTANT, LEGAL)
- is_staff
- is_active
- created_at
- updated_at
```

### Document
```python
- file
- user (ForeignKey to CustomUser)
- status (uploaded, processing, completed, failed)
- created_at
- updated_at
```

### DocumentAnalysis
```python
- document (OneToOneField)
- summary
- key_points
- topics
- created_at
```

---

## Testing

Run all authentication tests:
```bash
python manage.py test accounts
```

Run specific test class:
```bash
python manage.py test accounts.tests.UserRegistrationTestCase
```

With coverage:
```bash
coverage run --source='accounts' manage.py test accounts
coverage report -m
```

Test coverage includes:
- User registration
- JWT login
- Token refresh
- Profile management
- Role-based access control
- Document upload authentication

---

## Environment Variables

Create a `.env` file in the project root:

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT (optional - uses SECRET_KEY by default)
# JWT_SECRET_KEY=your-jwt-secret-key

# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## Next Steps

1. **Frontend Integration**
   - Implement user registration form
   - Implement login form
   - Store JWT tokens securely
   - Add token refresh logic
   - Implement role-based UI

2. **Enhanced Security**
   - Implement rate limiting
   - Add CORS configuration
   - Configure HTTPS
   - Set up secure cookie flags

3. **Additional Features**
   - Email verification
   - Password reset
   - User role assignments by admin
   - Audit logging
   - API key authentication

4. **Workflow Integration**
   - Implement workflow endpoints
   - Add role-based workflow permissions
   - Document routing by role

---

## Troubleshooting

### Migration Errors
```bash
# Reset migrations (development only)
python manage.py migrate accounts zero
python manage.py migrate
```

### Permission Denied
- Check user authentication: Send valid token in Authorization header
- Check user role: User's role must match endpoint requirements
- Check if user is_active: Inactive users cannot authenticate

### Token Expired
- Use refresh token: `POST /api/accounts/auth/token/refresh/`
- Extract refresh token from login response
- Send in request body: `{"refresh": "token_value"}`

---

## Production Deployment

1. Update `SECRET_KEY` via environment variable
2. Set `DEBUG=False`
3. Configure `ALLOWED_HOSTS`
4. Use PostgreSQL (already configured)
5. Set up Redis for caching/sessions
6. Configure CORS for your domain
7. Enable HTTPS/SSL
8. Set up automated backups
9. Configure email backend (for password reset)
10. Set up monitoring and logging

---

## Support

For detailed implementation information, see:
- `API_AUTHENTICATION.md` - API endpoints and usage
- `IMPLEMENTATION_GUIDE.md` - Technical deep dive
- `accounts/tests.py` - Test examples and usage patterns
