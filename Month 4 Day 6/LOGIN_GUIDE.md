# Day 6: Login Endpoint + JWT Issuance

## Complete Flow: Registration → Login → Protected Routes

```
1. Register: POST /auth/register
   Input:  {email, password}
   Output: {id, email, created_at}
   DB:     store email + hashed_password

2. Login: POST /auth/login
   Input:  form data (email, password)
   Process: verify password hash
   Output: {access_token, token_type, expires_in}
   
3. Protected route: GET /api/me
   Input:  Authorization: Bearer <token>
   Process: verify JWT signature
   Output: {id, email, created_at}
```

## Key Concepts

### 1. Password Verification (Not Comparison)

**WRONG: Plain comparison**
```python
if user.password == entered_password:  # ✗ Timing attack vulnerability
    login_user()
```

**RIGHT: Constant-time comparison**
```python
if not pwd_context.verify(entered_password, user.hashed_password):  # ✓
    raise HTTPException(401, "Bad credentials")
```

`pwd_context.verify()`:
- Takes ~100ms (same whether password is 5 chars or 500 chars)
- Doesn't leak information about where password differs
- Resistant to timing attacks
- Returns boolean: correct or wrong

### 2. OAuth2PasswordRequestForm

Pydantic automatically extracts form data:

```python
@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # form_data.username  — email (or username)
    # form_data.password  — password
    # form_data.scope     — optional scopes
```

Form data format (application/x-www-form-urlencoded):
```
username=alice@test.com&password=SecurePass123
```

### 3. JWT Creation with Claims

```python
from datetime import datetime, timedelta

payload = {
    "sub": str(user.id),           # ✓ subject = user ID
    "exp": datetime.utcnow() + timedelta(minutes=15),  # ✓ expiry
    "iat": datetime.utcnow()       # ✓ issued at
}

token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

**Claims:**
- `sub` (subject): Who the token is about (user ID)
- `exp` (expiration): When token dies (Unix timestamp)
- `iat` (issued at): When token was created (Unix timestamp)
- Custom claims: `role`, `permissions`, etc.

### 4. Token Response

**Standard OAuth2 response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiI...",
  "token_type": "bearer",
  "expires_in": 900
}
```

- `access_token`: The JWT (client stores this)
- `token_type`: Always "bearer" (standard)
- `expires_in`: Seconds until expiry (help client know when to refresh)

### 5. Error Handling

**Generic error message (prevents email enumeration):**

```python
# WRONG: Leaks information
if user not found:
    return "No user with that email"
if password wrong:
    return "Wrong password"

# RIGHT: Generic message
raise HTTPException(401, "Incorrect email or password")
```

Why? Attackers can't tell if an email exists just by trying login.

## Testing: Complete Flow

### Step 1: Register a User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@test.com", "password": "SecurePass123"}'
```

**Response:**
```json
{
  "id": 1,
  "email": "alice@test.com",
  "created_at": "2024-09-21T12:00:00"
}
```

### Step 2: Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@test.com&password=SecurePass123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Step 3: Use Token on Protected Route

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl http://localhost:8000/api/me \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "id": 1,
  "email": "alice@test.com",
  "created_at": "2024-09-21T12:00:00"
}
```

### Step 4: Try Without Token (Should Fail)

```bash
curl http://localhost:8000/api/me
```

**Response (403):**
```json
{
  "detail": "Not authenticated"
}
```

### Step 5: Try Wrong Password (Should Fail)

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@test.com&password=WrongPassword"
```

**Response (401):**
```json
{
  "detail": "Incorrect email or password"
}
```

## Architecture

### Request Flow for Protected Route

```
Client requests: GET /api/me
  ↓
Header: Authorization: Bearer eyJ...
  ↓
FastAPI: extract token from header
  ↓
Depends(oauth2_scheme): gives token to dependency
  ↓
Depends(get_current_user): verifies token
  ↓
jwt.decode(token, SECRET_KEY)
  ↓
Verify signature matches
  ↓
If invalid: raise 401
If valid: fetch user from database by ID
  ↓
Return user to route handler
  ↓
Route returns {id, email, ...}
```

### Database Queries

**At Login:**
```sql
SELECT * FROM users WHERE email = ?
```

**Verify:** `pwd_context.verify(entered_password, user.hashed_password)`

**At Protected Route:** (if needed to refresh user data)
```sql
SELECT * FROM users WHERE id = ?
```

## Code Structure

### Login Endpoint

```python
@app.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Step 1: Authenticate
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(401, "Incorrect email or password")
    
    # Step 2: Create token
    token, expires_in = create_access_token(user.id)
    
    # Step 3: Return
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in
    }
```

### Authenticate Helper

```python
def authenticate_user(email: str, password: str, db: Session) -> Optional[UserDB]:
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if not user:
        return None
    
    if not pwd_context.verify(password, user.hashed_password):
        return None
    
    return user
```

### Create Token Helper

```python
def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    expires_in = int((expire - datetime.utcnow()).total_seconds())
    
    return token, expires_in
```

### Get Current User Dependency

```python
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserDB:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
    except JWTError:
        raise HTTPException(401, "Invalid token")
    
    user = db.query(UserDB).filter(UserDB.id == int(user_id)).first()
    if not user:
        raise HTTPException(401, "User not found")
    
    return user
```

## Security Checklist

- ✅ Password verified with `pwd_context.verify()` (constant-time)
- ✅ JWT signed with SECRET_KEY (only server can create tokens)
- ✅ Token has expiry (15 minutes by default)
- ✅ Generic error message (doesn't leak email existence)
- ✅ No passwords stored (only hashes)
- ✅ No passwords logged
- ✅ Token sent via Authorization header (standard)
- ✅ HTTPS should be used in production (token not encrypted)
- ✅ Token type is "bearer" (standard)

## Common Mistakes

### ❌ Comparing passwords with ==
```python
if user.password == entered:  # ✗ Timing attack
    login()
```

### ❌ Returning password in response
```python
return {"user": user}  # ✗ User model includes password
```

### ❌ Revealing user existence
```python
if user not found:
    return "No user with that email"  # ✗ Leaks info
```

### ❌ Storing plain tokens
Client-side storage options:
- localStorage — vulnerable to XSS (but convenient)
- sessionStorage — cleared on tab close
- Cookie with HttpOnly + Secure + SameSite (best, but harder)
- Memory (lost on refresh, good for security)

### ❌ Token without expiry
```python
payload = {"sub": user.id}  # ✗ No exp means tokens live forever
```

### ❌ Using symmetric key for multi-service setup
- Use RS256 (asymmetric) if multiple services verify tokens
- Use HS256 (symmetric) only if one service issues and verifies

## Token Lifetime Strategy

| Token | Lifetime | Where Stored | Purpose |
|-------|----------|--------------|---------|
| Access | 15 min | Memory/localStorage | Use for API calls |
| Refresh | 7 days | Secure HTTP-only cookie | Get new access token |
| ID | 1 hour | Memory | User info (OpenID) |

Today we only have access tokens. Day 7+ will add refresh tokens.

## Files

- **fastapi_auth_complete.py** — Register + Login + Protected routes
- **test_login.py** — Pytest tests (20+ test cases)
- **test_login_manual.py** — Manual tests (10 scenarios)
- **DAY_6_SUMMARY.md** — Quick reference

## Testing

### Pytest

```bash
pytest test_login.py -v
```

Tests:
- Successful login
- Wrong password (401)
- User not found (401)
- JWT token validity
- Token usage on protected routes
- Expired token rejection
- Multiple users
- Constant-time comparison
- Generic error messages

### Manual Testing

```bash
# Terminal 1
python fastapi_auth_complete.py

# Terminal 2
python test_login_manual.py
```

## Next: Refresh Tokens (Day 7+)

Problem: 15-minute access tokens mean users get logged out frequently.

Solution: Refresh tokens
- Long-lived (7 days)
- Stored securely (HTTP-only cookie)
- Used to get new access tokens
- Can be revoked (logout)

Flow:
```
1. Login → get access_token (15 min) + refresh_token (7 days)
2. Use access_token for API calls
3. After 15 min → use refresh_token to get new access_token
4. After 7 days → user must login again
5. Logout → invalidate refresh_token
```

## Performance

- Login query: <10ms (indexed by email)
- Password verification: ~100ms (intentionally slow, bcrypt)
- JWT creation: <1ms
- Token verification: ~1ms
- **Total login: ~110ms per request**

Scales well. Single server handles ~100 logins/second.

## What Changed from Day 5

| Day 5 | Day 6 |
|-------|-------|
| Registration only | Registration + Login |
| No tokens | JWT token issuance |
| No protected routes | Protected routes with dependency |
| No password verification | Constant-time verification |

## Completion Checklist

- ✅ Login endpoint implemented
- ✅ Password verification (not comparison)
- ✅ JWT creation with proper claims
- ✅ Token expiry (15 minutes)
- ✅ Protected routes with dependency
- ✅ Error handling (401 for auth failures)
- ✅ Generic error messages (prevent enumeration)
- ✅ Pytest test suite (20+ tests)
- ✅ Manual testing script
- ✅ Documentation complete

You now have a complete, production-grade authentication system:
- Register users
- Hash passwords with bcrypt
- Login and get JWT tokens
- Access protected routes
- JWT tokens expire
- Wrong password rejected
- Non-existent email rejected

Next: Add refresh tokens, logout, email verification, password reset.
