# API Authentication & Authorization Guide

## Overview

This Django REST API uses **JWT (JSON Web Token) authentication** with role-based access control (RBAC).

### User Roles
- **ADMIN**: Full system access, manage users
- **HR**: HR-related permissions
- **ACCOUNTANT**: Financial and accounting permissions
- **LEGAL**: Legal document and compliance permissions

---

## Authentication Flow

### 1. User Registration

**Endpoint:** `POST /api/accounts/users/`

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "password_confirm": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "HR"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "HR",
  "is_active": true,
  "created_at": "2024-05-03T10:00:00Z",
  "updated_at": "2024-05-03T10:00:00Z"
}
```

**Validation:**
- Email must be unique
- Password must match password_confirm
- Role must be one of: ADMIN, HR, ACCOUNTANT, LEGAL
- Minimum password length is enforced by Django validators

---

### 2. User Login (Obtain JWT Token)

**Endpoint:** `POST /api/accounts/auth/token/`

Authenticate and receive access/refresh tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "HR",
    "is_active": true
  }
}
```

**Token Details:**
- **Access Token**: Valid for 60 minutes, used in API requests
- **Refresh Token**: Valid for 7 days, used to get a new access token
- Tokens are included in token response for convenience

---

### 3. Refresh Access Token

**Endpoint:** `POST /api/accounts/auth/token/refresh/`

Get a new access token using the refresh token.

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## API Authorization

### Using the Access Token

Include the access token in the `Authorization` header:

```
Authorization: Bearer {access_token}
```

Example with curl:
```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
     http://localhost:8000/api/accounts/users/me/
```

Example with Python requests:
```python
import requests

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/accounts/users/me/", headers=headers)
```

---

## User Endpoints

All endpoints require authentication unless otherwise noted.

### Get Current User Profile

**Endpoint:** `GET /api/accounts/users/me/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "HR",
  "is_active": true,
  "created_at": "2024-05-03T10:00:00Z",
  "updated_at": "2024-05-03T10:00:00Z"
}
```

---

### Update User Profile

**Endpoint:** `PATCH /api/accounts/users/{id}/`

Update your own profile (or admin can update any profile).

**Request:**
```json
{
  "first_name": "Jonathan",
  "last_name": "Smith"
}
```

**Response (200 OK):**
```json
{
  "email": "user@example.com",
  "first_name": "Jonathan",
  "last_name": "Smith",
  "role": "HR"
}
```

---

### Change Password

**Endpoint:** `POST /api/accounts/users/change_password/`

**Request:**
```json
{
  "old_password": "securepassword123",
  "new_password": "newsecurepassword456",
  "new_password_confirm": "newsecurepassword456"
}
```

**Response (200 OK):**
```json
{
  "detail": "Password changed successfully."
}
```

---

### List All Users (Admin Only)

**Endpoint:** `GET /api/accounts/users/`

Only accessible to admin users.

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "role": "ADMIN",
    "is_active": true,
    "created_at": "2024-05-03T09:00:00Z",
    "updated_at": "2024-05-03T09:00:00Z"
  },
  {
    "id": 2,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "HR",
    "is_active": true,
    "created_at": "2024-05-03T10:00:00Z",
    "updated_at": "2024-05-03T10:00:00Z"
  }
]
```

---

## Document Endpoints

All document endpoints require authentication.

### Upload Document

**Endpoint:** `POST /api/documents/upload`

Upload a PDF document for processing.

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Request:**
```
file: <binary PDF file>
```

**Response (201 Created):**
```json
{
  "id": 1,
  "status": "uploaded",
  "message": "Document uploaded successfully. Processing started."
}
```

---

### List Documents

**Endpoint:** `GET /api/documents/`

Get all documents uploaded by the current user.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "file": "http://localhost:8000/media/documents/example.pdf",
    "user": 1,
    "user_email": "user@example.com",
    "status": "completed",
    "created_at": "2024-05-03T10:00:00Z",
    "updated_at": "2024-05-03T10:05:00Z",
    "analysis": {
      "document": 1,
      "summary": "Document summary...",
      "key_points": ["Point 1", "Point 2"],
      "topics": ["Topic 1", "Topic 2"],
      "created_at": "2024-05-03T10:05:00Z"
    }
  }
]
```

---

### Get Document Details

**Endpoint:** `GET /api/documents/{id}/`

Get a specific document with analysis (if completed).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "file": "http://localhost:8000/media/documents/example.pdf",
  "user": 1,
  "user_email": "user@example.com",
  "status": "completed",
  "created_at": "2024-05-03T10:00:00Z",
  "updated_at": "2024-05-03T10:05:00Z",
  "analysis": {
    "document": 1,
    "summary": "Document summary...",
    "key_points": ["Point 1", "Point 2"],
    "topics": ["Topic 1", "Topic 2"],
    "created_at": "2024-05-03T10:05:00Z"
  }
}
```

---

### Get Document Status

**Endpoint:** `GET /api/documents/{id}/status/`

Quick status check without full document data.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "status": "processing"
}
```

**Status Values:**
- `uploaded`: Initial state after upload
- `processing`: Document is being analyzed
- `completed`: Analysis complete
- `failed`: Processing failed

---

## Error Responses

### 401 Unauthorized (Missing/Invalid Token)

```json
{
  "detail": "Authentication credentials were not provided."
}
```

or

```json
{
  "detail": "Given token not valid for any token type"
}
```

### 403 Forbidden (Insufficient Permissions)

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found

```json
{
  "error": "Document not found"
}
```

### 400 Bad Request

```json
{
  "field_name": ["Error message"]
}
```

---

## JWT Token Claims

The access token includes the following claims:

```json
{
  "token_type": "access",
  "exp": 1714833600,
  "iat": 1714830000,
  "jti": "abc123...",
  "user_id": 1,
  "email": "user@example.com",
  "role": "HR"
}
```

You can decode the token to check:
- Token expiration (`exp`)
- User ID and role
- Token type

---

## Best Practices

1. **Store tokens securely**: Use secure HTTP-only cookies or secure storage
2. **Refresh tokens regularly**: Use the refresh endpoint before access token expires
3. **Handle token expiration**: Implement refresh logic in your frontend
4. **Use HTTPS**: Always use HTTPS in production
5. **Rotate refresh tokens**: Each refresh invalidates the old refresh token
6. **Check token expiration**: Implement client-side token expiration checks

---

## Example Implementation

### JavaScript/React

```javascript
const API_BASE_URL = "http://localhost:8000/api";

// 1. Register
async function register() {
  const response = await fetch(`${API_BASE_URL}/accounts/users/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: "user@example.com",
      password: "password123",
      password_confirm: "password123",
      first_name: "John",
      role: "HR"
    })
  });
  return await response.json();
}

// 2. Login
async function login() {
  const response = await fetch(`${API_BASE_URL}/accounts/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: "user@example.com",
      password: "password123"
    })
  });
  const data = await response.json();
  localStorage.setItem("access_token", data.access);
  localStorage.setItem("refresh_token", data.refresh);
  return data;
}

// 3. Get user profile
async function getProfile() {
  const token = localStorage.getItem("access_token");
  const response = await fetch(`${API_BASE_URL}/accounts/users/me/`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  return await response.json();
}

// 4. Upload document
async function uploadDocument(file) {
  const token = localStorage.getItem("access_token");
  const formData = new FormData();
  formData.append("file", file);
  
  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}` },
    body: formData
  });
  return await response.json();
}

// 5. Refresh token
async function refreshToken() {
  const refreshToken = localStorage.getItem("refresh_token");
  const response = await fetch(`${API_BASE_URL}/accounts/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken })
  });
  const data = await response.json();
  localStorage.setItem("access_token", data.access);
  return data;
}
```

---

## Workflow Example

```
1. User registers: POST /api/accounts/users/
2. User logs in: POST /api/accounts/auth/token/
3. Receive access + refresh tokens
4. Upload document: POST /api/documents/upload (with access token)
5. Poll status: GET /api/documents/{id}/status/ (with access token)
6. When access token expires:
   - Use refresh token: POST /api/accounts/auth/token/refresh/
   - Get new access token
   - Continue with API calls
```

---

## Environment Setup

### Create .env file

```bash
# Django
SECRET_KEY=your-secret-key

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT (optional - uses SECRET_KEY by default)
JWT_SECRET_KEY=your-jwt-secret-key
```

### Configuration

All JWT settings are in `django_ai_doc_processing/settings.py`:
- Access token lifetime: 60 minutes
- Refresh token lifetime: 7 days
- Token rotation: Enabled
- Algorithm: HS256
