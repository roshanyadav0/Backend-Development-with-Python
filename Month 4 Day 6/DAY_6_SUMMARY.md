# Day 6: Login Endpoint + JWT Issuance

## What You Built

A complete login system that:
- ✅ Accepts email + password (OAuth2 form data)
- ✅ Queries database for user
- ✅ Verifies password hash (constant-time, bcrypt)
- ✅ Creates JWT with proper claims (sub, exp, iat)
- ✅ Returns token response (access_token, token_type, expires_in)
- ✅ Protects routes with token verification
- ✅ Rejects wrong password (401)
- ✅ Rejects non-existent email (401 with generic message)

## The Complete Flow

```
User Registration:
  POST /auth/register
  Input:  {email, password}
  ↓
  Hash password (bcrypt)
  ↓
  Store: email + hashed_password
  ↓
  Response: {id, email, created_at}

User Login:
  POST /auth/login
  Input:  form data (email, password)
  ↓
  Query: SELECT * FROM users WHERE email = ?
  ↓
  Verify: pwd_context.verify(entered_password, stored_hash)
  ↓
  If invalid: 401 (generic message)
  If valid: Create JWT
  ↓
  JWT = sign({sub: user_id, exp: +15min, iat: now})
  ↓
  Response: {access_token, token_type, expires_in}

Access Protected Route:
  GET /api/me
  Header: Authorization: Bearer {token}
  ↓
  Extract token from header
  ↓
  Verify: jwt.decode(token, SECRET_KEY)
  ↓
  Check: exp > now? (not expired)
  ↓
  If invalid: 401
  If valid: Fetch user from DB
  ↓
  Response: {id, email, created_at}
```

## Key Patterns

### 1. Password Verification (Constant-Time)

```python
def authenticate_user(email: str, password: str, db: Session) -> Optional[UserDB]:
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if not user:
        return None
    
    # ✓ Use pwd_context.verify() — constant-time comparison
    if not pwd_context.verify(password, user.hashed_password):
        return None
    
    return user
```

Why constant-time?
- Prevent timing attacks (attackers can't learn where password differs)
- Same ~100ms whether password is 5 chars or 500 chars
- Resists side-channel attacks

### 2. JWT Creation

```python
def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    payload = {
        "sub": str(user_id),              # ✓ Subject (who token is about)
        "exp": expire,                    # ✓ Expiration (when it dies)
        "iat": datetime.utcnow()          # ✓ Issued at (creation time)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    expires_in = int((expire - datetime.utcnow()).total_seconds())
    
    return token, expires_in
```

Claims:
- `sub`: User ID (server uses this to identify user later)
- `exp`: Expiration timestamp (token dead after this)
- `iat`: Creation timestamp (RFC standard)
- Custom: `role`, `permissions`, etc. (add as needed)

### 3. Protected Route with Dependency

```python
@app.get("/api/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserDB = Depends(get_current_user)):
    """
    Protected endpoint.
    Depends(get_current_user) automatically:
      1. Extracts token from Authorization header
      2. Verifies JWT signature
      3. Checks expiry
      4. Fetches user from database
      5. Returns user or 401
    """
    return current_user
```

FastAPI's dependency injection runs before the route:
- If dependency succeeds → user is passed to route
- If dependency fails → route never runs, returns 401

### 4. Generic Error Message (Prevent Email Enumeration)

```python
# WRONG: Leaks information
if not user:
    raise HTTPException(401, "No user with that email")

if not pwd_context.verify(password, user.hashed_password):
    raise HTTPException(401, "Wrong password")

# RIGHT: Generic message
raise HTTPException(401, "Incorrect email or password")
```

Why? Attackers can't enumerate valid emails by trying login and checking error message.

## HTTP Flow

### Login (POST /auth/login)

**Request:**
```
POST /auth/login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=alice@test.com&password=SecurePass123
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNjI1MDAwMDAwfQ.signature...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Incorrect email or password"
}
```

### Protected Route (GET /api/me)

**Request (with token):**
```
GET /api/me HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "alice@test.com",
  "created_at": "2024-09-21T12:00:00"
}
```

**Response (missing token, 403 Forbidden):**
```json
{
  "detail": "Not authenticated"
}
```

**Response (invalid/expired token, 401 Unauthorized):**
```json
{
  "detail": "Could not validate credentials"
}
```

## Testing Coverage

### Pytest Tests (20+ cases)

```bash
pytest test_login.py -v
```

- ✅ Successful login with correct credentials
- ✅ Login returns valid JWT
- ✅ Wrong password (401)
- ✅ Non-existent email (401, generic message)
- ✅ Protected route with valid token (200)
- ✅ Protected route without token (403)
- ✅ Protected route with invalid token (401)
- ✅ Protected route with expired token (401)
- ✅ Multiple users (each gets own token)
- ✅ Token expiry time is correct
- ✅ Token contains user ID
- ✅ Generic error prevents enumeration
- ✅ GET /auth/login not allowed (405)

### Manual Tests (10 scenarios)

```bash
python test_login_manual.py
```

- Complete flow: register → login → protected route
- Wrong password rejection
- Non-existent email rejection
- Multiple users can login independently
- Tokens are different per login
- Corrupted tokens rejected
- Token usage on multiple protected routes

## Security Layers

| Layer | Implementation |
|-------|-----------------|
| Transport | HTTPS (TLS) — encrypt in flight |
| Input | Pydantic validates email format |
| Auth | Constant-time password verification |
| Token | JWT signed (tampering detected) |
| Token expiry | 15 minutes (limits damage if stolen) |
| DB | Bcrypt hashes (brute force is slow) |
| Error handling | Generic message (no info leak) |
| Output | No password/hash in response |

## Performance

- Query user by email: ~1ms (indexed)
- Verify password: ~100ms (intentionally slow, bcrypt)
- Create JWT: <1ms
- Verify JWT: <1ms
- **Total login: ~102ms**

Scales:
- Single server: ~100 logins/second
- 10 servers: ~1000 logins/second
- Limited by database + password hashing (not CPU)

## JWT Anatomy

```
Header.Payload.Signature

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaWF0IjoxNjI1LCJleHAiOjE2MjU5MDB9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

Header (base64):
  {
    "alg": "HS256",      # Algorithm (HMAC-SHA256)
    "typ": "JWT"        # Type
  }

Payload (base64):
  {
    "sub": "1",         # Subject (user ID)
    "iat": 1625,        # Issued at
    "exp": 1625900      # Expiration
  }

Signature (HMAC):
  HMAC(SECRET_KEY, header.payload)
```

Only the server knows SECRET_KEY, so only the server can create valid signatures.

## Code Structure

```
fastapi_auth_complete.py:
  ├─ Database setup (SQLAlchemy)
  ├─ Password hashing (bcrypt via passlib)
  ├─ Pydantic schemas (input/output validation)
  ├─ Helper functions:
  │  ├─ authenticate_user() — verify password
  │  ├─ create_access_token() — create JWT
  │  └─ get_current_user() — dependency for protected routes
  └─ Endpoints:
     ├─ POST /auth/register — create user
     ├─ POST /auth/login — login, get token
     ├─ GET /api/me — protected route
     └─ GET /api/profile — another protected route
```

## What Changed from Day 5

| Day 5 | Day 6 |
|-------|-------|
| Registration only | Registration + Login |
| No authentication | Password verification |
| No JWT | JWT token creation |
| No protected routes | Dependency-protected routes |
| No error handling | Proper 401/403 responses |

## Common Mistakes Fixed

### ❌ Plain password comparison → ✅ pwd_context.verify()
```python
# WRONG
if user.password == entered:  # Timing attack

# RIGHT
if not pwd_context.verify(entered, user.hash):  # Constant-time
```

### ❌ Revealing user existence → ✅ Generic error
```python
# WRONG
if not user: return "User not found"  # Leaks email existence
if not verify: return "Wrong password"  # Different error

# RIGHT
raise HTTPException(401, "Incorrect email or password")  # Same error
```

### ❌ No token expiry → ✅ 15-minute expiry
```python
# WRONG
payload = {"sub": user.id}  # Stolen token works forever

# RIGHT
payload = {"sub": user.id, "exp": datetime.utcnow() + timedelta(minutes=15)}
```

### ❌ Returning password → ✅ Only safe fields
```python
# WRONG
return user  # Includes password field

# RIGHT
return UserResponse(id=user.id, email=user.email, created_at=user.created_at)
```

## Files Delivered

1. **fastapi_auth_complete.py** (230 lines)
   - Register + Login endpoints
   - Protected route with dependency
   - Password verification
   - JWT creation

2. **test_login.py** (350 lines)
   - Pytest test suite
   - 20+ test cases
   - Happy path + error paths
   - Security tests (timing, enumeration prevention)

3. **test_login_manual.py** (330 lines)
   - Manual testing without pytest
   - 10 complete scenarios
   - Debug-friendly output

4. **LOGIN_GUIDE.md** (400 lines)
   - Complete reference
   - Architecture diagrams
   - Curl examples
   - Common mistakes

## Quick Start

```bash
# 1. Install
pip install fastapi sqlalchemy passlib[bcrypt] pydantic[email] pytest httpx python-jose[cryptography]

# 2. Start server
python fastapi_auth_complete.py

# 3. Test (another terminal)
python test_login_manual.py

# OR
pytest test_login.py -v

# 4. Browse API
Open http://localhost:8000/docs
```

## Next Steps (Day 7+)

- **Refresh tokens** — Long-lived tokens to get new access tokens
- **Logout** — Revoke refresh tokens, invalidate sessions
- **Email verification** — Send confirmation link on signup
- **Password reset** — Secure token-based password reset
- **Rate limiting** — Prevent brute force on login
- **2FA** — Two-factor authentication

## Completion Checklist

- ✅ Login endpoint implemented (POST /auth/login)
- ✅ Password verification (constant-time, bcrypt)
- ✅ JWT creation with proper claims (sub, exp, iat)
- ✅ Token response format (access_token, token_type, expires_in)
- ✅ Protected routes with dependency injection
- ✅ Error handling (401 for auth failures, 403 for missing token)
- ✅ Generic error messages (prevent enumeration)
- ✅ Pytest test suite (20+ tests)
- ✅ Manual testing script
- ✅ Documentation complete

## Summary

You now have a production-grade login system:

1. **User Lifecycle**
   - Register: Email + password → store hashed
   - Login: Email + password → verify hash → get JWT
   - Access: JWT in Authorization header → protected routes

2. **Security**
   - Passwords never stored plain (bcrypt)
   - Password verification is constant-time (timing attacks)
   - Tokens expire (limit damage if stolen)
   - Generic errors (prevent email enumeration)
   - JWT signed (tampering detected)

3. **Integration**
   - All pieces work together seamlessly
   - Combine Days 1-6 for complete system
   - Ready for production (with HTTPS)

Combined with Days 1-5, you have authentication that:
- Accepts user credentials securely
- Hashes passwords properly
- Issues short-lived JWT tokens
- Protects API routes with tokens
- Rejects invalid/expired tokens
- Provides proper error responses

This is a real, usable authentication system.
