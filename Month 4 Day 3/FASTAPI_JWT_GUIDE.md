# FastAPI OAuth2PasswordBearer + JWT Setup — Quick Reference

## Installation

```bash
pip install fastapi uvicorn python-jose[cryptography] pydantic
```

## The 3 Core Components

### 1. OAuth2PasswordBearer — The Scheme

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
```

This tells FastAPI:
- Where to get tokens: `POST /auth/login`
- How to accept them: `Authorization: Bearer <token>` header
- Automatically adds a "lock" icon in Swagger UI with an "Authorize" button
- Generates OpenAPI/Swagger schema automatically

### 2. Login Endpoint — Issue Tokens

```python
from fastapi.security import OAuth2PasswordRequestForm

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Bad credentials")
    
    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}
```

`OAuth2PasswordRequestForm` gives you:
- `username` — from form data
- `password` — from form data  
- `scope` — optional scopes (rarely used with JWTs)

### 3. Protected Routes — Verify Tokens

```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency that:
    1. Extracts the token from Authorization header
    2. Verifies the JWT signature
    3. Returns the current user
    4. Raises 401 if token is missing/invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return get_user_from_db(username)

@app.get("/api/me")
async def read_me(current_user = Depends(get_current_user)):
    # get_current_user runs automatically
    # If token is invalid, FastAPI returns 401 immediately
    # If valid, current_user is the user object
    return current_user
```

## How Dependency Injection Works

```python
# Define a dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Validate token, return user
    return user

# Use it in a route
@app.get("/api/protected")
async def protected_route(current_user = Depends(get_current_user)):
    # FastAPI runs get_current_user() before this route
    # If it fails (raises HTTPException), route never runs
    # If it succeeds, current_user is the return value
    return {"user": current_user}
```

**What FastAPI does:**
1. Client hits `/api/protected` with `Authorization: Bearer <token>`
2. FastAPI calls `oauth2_scheme` to extract the token
3. FastAPI calls `get_current_user(token=...)`
4. `get_current_user` validates the token, returns user (or raises 401)
5. Route handler receives `current_user` with the user data
6. Client gets 200 + response, or 401 + error

## Complete Login → Protected Route Flow

```
1. Client POST /auth/login (username, password)
   ↓
2. Server validates credentials
   ↓
3. Server creates JWT: {sub: "alice", exp: 1234567890}
   ↓
4. Server returns {access_token: "eyJh...", token_type: "bearer"}
   ↓
5. Client stores token (localStorage, sessionStorage, memory)
   ↓
6. Client GET /api/me (Header: Authorization: Bearer eyJh...)
   ↓
7. FastAPI extracts token from header
   ↓
8. get_current_user() verifies signature
   ↓
9. JWT valid → return user object
   ↓
10. Route handler uses user, returns 200 + data
```

## Testing with curl

```bash
# 1. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=alice"

# Response:
# {"access_token":"eyJh...","token_type":"bearer","expires_in":1800}

# 2. Use the token
curl http://localhost:8000/api/me \
  -H "Authorization: Bearer eyJh..."

# Response (if token valid):
# {"username":"alice","email":"alice@example.com",...}

# 3. Test without token (should fail)
curl http://localhost:8000/api/me

# Response (401):
# {"detail":"Not authenticated"}
```

## Testing with Swagger UI

1. Start server: `python fastapi_jwt_app.py`
2. Open http://localhost:8000/docs
3. Click the lock icon on any protected route
4. Click "Authorize"
5. Paste token in the field
6. Click routes to test

The "Authorize" button exists because of `OAuth2PasswordBearer(tokenUrl="/auth/login")` — FastAPI auto-generates it.

## Common Mistakes & Fixes

### ❌ Missing `Depends()`
```python
# WRONG — dependency is defined but never called
async def read_me(current_user: User):
    return current_user  # TypeError: current_user is not defined

# RIGHT — dependency is called by FastAPI
async def read_me(current_user: User = Depends(get_current_user)):
    return current_user  # current_user is the user object
```

### ❌ Forgetting token type
```python
# WRONG — server issues token without type
return {"access_token": token}  # Swagger tries to use this and fails

# RIGHT — include token_type
return {"access_token": token, "token_type": "bearer"}
```

### ❌ Wrong Authorization header format
```
# WRONG
Authorization: eyJh...  # Server doesn't know this is a Bearer token

# RIGHT
Authorization: Bearer eyJh...  # Server parses this correctly
```

### ❌ Not catching token errors
```python
# WRONG — if token is invalid, the exception bubbles and fastapi returns 500
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # If JWT is corrupted, JWTError is raised and unhandled

# RIGHT — catch JWT errors and return 401
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## Architecture Diagram

```
┌─────────┐               ┌──────────────┐
│ Client  │               │ FastAPI      │
└────┬────┘               └──────┬───────┘
     │                           │
     ├──POST /auth/login────────→│
     │  (username, password)      │
     │                           │ Authenticate user
     │                           │ Create JWT
     │←─── access_token ─────────┤
     │    (expires_in: 3600)      │
     │                           │
     │ Store token in            │
     │ localStorage              │
     │                           │
     ├──GET /api/me─────────────→│
     │  Authorization: Bearer X   │
     │                           │ Extract token
     │                           │ Verify signature
     │                           │ Return user
     │←────── user data ─────────┤
     │    (200 OK)                │
     │                           │
     │ [Later...]                │
     │                           │
     ├──GET /api/profile────────→│
     │  Authorization: Bearer X   │
     │                           │ Token still valid
     │←──── profile data ────────┤
     │    (200 OK)                │
     │                           │
     │ [After 1 hour...]         │
     │                           │
     ├──GET /api/profile────────→│
     │  Authorization: Bearer X   │
     │                           │ Token expired
     │←──── 401 Unauthorized ────┤
     │   (refresh token needed)   │
```

## Next Steps (Day 4)

- Refresh tokens (get new access token without re-login)
- Logout (token blacklist or invalidation)
- Scopes & permissions (fine-grained access control)
- Role-based access control (RBAC)
