# Day 12: OAuth Callback Handler — Quick Reference

---

## 🎯 What We're Building Today

```python
@app.get('/auth/google/callback')
async def google_callback(code: str, state: str, request: Request):
    """
    Google redirects here after user authorizes
    We now have an authorization code (single-use)
    We exchange it for tokens and create our JWT
    """
    # STEP 1: Validate state (CSRF protection)
    # STEP 2: Exchange code for Google token
    # STEP 3: Extract user info from ID token
    # STEP 4: Find or create user in database
    # STEP 5: Issue our own JWT token
    # STEP 6: Set cookie and redirect to dashboard
```

---

## 🚀 The 6 Steps (Code Examples)

### STEP 1: Validate State (CSRF Protection)

```python
# Get state from cookie
cookie_state = request.cookies.get('oauth_state')

# Verify it matches
if cookie_state != state:
    raise HTTPException(status_code=400, detail='CSRF attack')

# Validate it's not expired or already used
if not state_store.validate(cookie_state):
    raise HTTPException(status_code=400, detail='Invalid state')
```

**Why:** Prevents CSRF attacks where attacker tricks user into authorizing attacker's account

---

### STEP 2: Exchange Code for Token

```python
# Make backend-to-backend request to Google
token_response = await httpx.AsyncClient().post(
    'https://oauth2.googleapis.com/token',
    data={
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,  # ← NEVER in browser!
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': GOOGLE_REDIRECT_URI
    }
)

# Returns:
# {
#   "access_token": "ya29.a0AfH6SMBu...",
#   "id_token": "eyJhbGc...",
#   "refresh_token": "1//0g...",
#   "expires_in": 3599
# }
```

**Key:** `client_secret` must be on BACKEND, never exposed to browser

---

### STEP 3: Extract User Info

**Option A: Decode ID Token (Recommended)**
```python
# ID token is JWT with user info (no extra API call needed)
payload = jwt.decode(
    token_response['id_token'],
    options={'verify_signature': False}
)

# Now you have:
google_id = payload['sub']           # Google's user ID
email = payload['email']             # User's email
name = payload['name']               # User's name
picture = payload['picture']         # Profile pic
email_verified = payload['email_verified']
```

**Option B: Call UserInfo Endpoint (Extra API call)**
```python
response = await httpx.AsyncClient().get(
    'https://www.googleapis.com/oauth2/v1/userinfo',
    headers={'Authorization': f'Bearer {access_token}'}
)

user_data = response.json()
# Returns same fields as Option A
```

**Recommendation:** Use Option A (decode ID token) - faster, no extra API call

---

### STEP 4: Find or Create User

```python
# Try to find existing user
user = user_db.find_by_google_id(google_id)

if user:
    # Existing user - update last login
    user_db.update_last_login(user.id)
    print(f'Welcome back, {email}!')
else:
    # New user - create in database
    user = user_db.create_user(
        google_id=google_id,
        email=email,
        name=name,
        picture=picture
    )
    print(f'New user registered: {email}')
```

**Database Schema:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    picture VARCHAR(2048),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    INDEX (google_id),
    INDEX (email)
);
```

---

### STEP 5: Issue Your Own JWT (Don't Use Google's Token)

```python
# ❌ WRONG: Store Google's access_token
#    - Expires quickly
#    - Can be revoked
#    - Only works for Google APIs

# ✅ RIGHT: Issue your own JWT
payload = {
    'user_id': user.id,      # YOUR user ID (not Google's)
    'email': user.email,
    'name': user.name,
    'iat': datetime.utcnow(),
    'exp': datetime.utcnow() + timedelta(hours=24)
}

jwt_token = jwt.encode(payload, YOUR_SECRET, algorithm='HS256')

# Returns: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Why your own JWT:**
- ✓ Represents permission to YOUR app (not Google's)
- ✓ You control expiration
- ✓ Works for all your services
- ✓ Doesn't depend on Google being up
- ✓ Stateless (can validate without DB)

---

### STEP 6: Set Cookie and Redirect

```python
response = RedirectResponse(url='/dashboard', status_code=302)

# Set JWT in secure httpOnly cookie
response.set_cookie(
    'access_token',
    jwt_token,
    max_age=3600,           # 1 hour
    httponly=True,          # Prevent XSS
    secure=True,            # HTTPS only (production)
    samesite='strict'       # CSRF protection
)

# Clean up oauth_state cookie
response.delete_cookie('oauth_state')

return response

# User is now logged in! 🎉
```

---

## 📊 Token Comparison

| Aspect | Google's Token | Your JWT |
|--------|---|---|
| **Lifetime** | ~1 hour | 24 hours (configurable) |
| **Refresh** | Need refresh_token | No, just issue new one |
| **Revocation** | Can be revoked by Google | Full control |
| **Scope** | Only Google APIs | Your entire app |
| **Dependency** | On Google's service | Self-contained |
| **When to use** | Never store long-term | Always use for your app |

**Rule of thumb:**
- Google's token: Use once on callback, then throw away
- Your JWT: Use for all authenticated requests

---

## 🔐 Security Checklist

```python
# ✅ Cookie Security
response.set_cookie(
    'access_token',
    jwt_token,
    httponly=True,      # ✓ Prevent XSS (JS can't access)
    secure=True,        # ✓ HTTPS only (production)
    samesite='strict',  # ✓ CSRF protection
    max_age=3600        # ✓ Short lifetime
)

# ✅ State Validation
if cookie_state != state:
    raise Error('CSRF attack')

if state_store.validate(state) == False:
    raise Error('Invalid/expired state')

# ✅ Secret Management
GOOGLE_CLIENT_SECRET        # Backend only (never browser)
JWT_SECRET                  # Backend only
# Store in environment variables or secrets vault
```

---

## 🐛 Error Handling

### Invalid Grant (Code Expired)
```
Google returns: error=invalid_grant
Reason: Code expired (~10 min) or already used
Action: Ask user to login again
```

### Invalid Client
```
Google returns: error=invalid_client
Reason: Wrong client_id or client_secret
Action: Check credentials in .env
```

### Missing Email
```
ID token missing email field
Action: Require email scope or reject user
```

### Invalid JWT
```
JWT decode fails
Reason: Wrong secret or corrupted token
Action: Ask user to login again
```

---

## 🧪 Testing

### Unit Test: Token Exchange
```python
def test_exchange_code_returns_tokens():
    """Code exchange should return valid tokens"""
    tokens = exchange_code_for_token('auth_code')
    
    assert 'access_token' in tokens
    assert 'id_token' in tokens
    assert 'expires_in' in tokens
```

### Unit Test: ID Token Decode
```python
def test_decode_id_token():
    """ID token should decode to user info"""
    payload = {
        'sub': '123',
        'email': 'user@example.com'
    }
    
    id_token = jwt.encode(payload, 'secret')
    decoded = jwt.decode(id_token, options={'verify_signature': False})
    
    assert decoded['email'] == 'user@example.com'
```

### Unit Test: Find or Create
```python
def test_find_or_create_user():
    """First login creates user, second login finds user"""
    
    # First login
    user1, is_new1 = db.find_or_create(google_id='123')
    assert is_new1 == True
    
    # Second login
    user2, is_new2 = db.find_or_create(google_id='123')
    assert is_new2 == False
    assert user1.id == user2.id
```

### Unit Test: JWT Verification
```python
def test_jwt_verification():
    """Valid JWT should verify"""
    token = jwt.encode({'user_id': '123'}, 'secret')
    payload = jwt.decode(token, 'secret', algorithms=['HS256'])
    
    assert payload['user_id'] == '123'
```

---

## 💾 Database Setup

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    picture VARCHAR(2048),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    
    INDEX idx_google_id (google_id),
    INDEX idx_email (email)
);
```

### Sessions Table (Optional)
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    jwt_token_hash VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
);
```

---

## 📈 Request Flow Diagram

```
1. User clicks login
        ↓
2. Redirected to Google (/auth/google/login)
        ↓
3. User authorizes on Google
        ↓
4. Google redirects to /auth/google/callback with code + state
        ↓
5. VALIDATE STATE (CSRF check)
        ↓
6. EXCHANGE CODE → Get tokens from Google
        ↓
7. DECODE ID TOKEN → Extract user info
        ↓
8. FIND_OR_CREATE USER → Check database
        ↓
9. ISSUE JWT → Your own token
        ↓
10. SET COOKIE → httpOnly, secure, short-lived
        ↓
11. REDIRECT to /dashboard
        ↓
12. User now authenticated ✓
```

---

## ⚡ Performance Tips

```python
# ✓ Good: Decode ID token (already have it)
user_info = jwt.decode(id_token, options={'verify_signature': False})

# ✗ Slow: Call /userinfo endpoint (extra API call)
user_info = await get_userinfo(access_token)

# ✓ Good: Find user by Google ID (indexed lookup)
user = db.find_by_google_id(google_id)

# ✓ Good: Issue JWT once (reuse for requests)
jwt_token = jwt.encode(payload, secret)

# ✗ Bad: Exchange token on every request
# (Do it once on callback, keep JWT in cookie)
```

---

## 🚀 Production Checklist

- [ ] Set `secure=True` on cookies (HTTPS only)
- [ ] Use real database (not mock)
- [ ] Rotate JWT_SECRET regularly
- [ ] Add rate limiting on callback endpoint
- [ ] Log successful logins
- [ ] Monitor failed login attempts
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Add request tracing
- [ ] Test full flow end-to-end
- [ ] Set up monitoring/alerting

---

## 📝 Complete Example

```python
@app.get('/auth/google/callback')
async def google_callback(code: str, state: str, request: Request):
    """Complete callback handler"""
    
    # 1. Validate state
    if request.cookies.get('oauth_state') != state:
        raise HTTPException(status_code=400, detail='CSRF')
    
    # 2. Exchange code
    tokens = await token_exchanger.exchange_code_for_token(code)
    
    # 3. Decode ID token
    user_info = UserInfoExtractor.decode_id_token(tokens['id_token'])
    
    # 4. Find or create user
    user, is_new = user_manager.find_or_create(
        google_id=user_info['google_id'],
        email=user_info['email'],
        name=user_info['name']
    )
    
    # 5. Issue JWT
    jwt_token = jwt_manager.generate_token(
        user_id=user.id,
        email=user.email,
        name=user.name
    )
    
    # 6. Set cookie and redirect
    response = RedirectResponse(url='/dashboard', status_code=302)
    response.set_cookie(
        'access_token',
        jwt_token,
        httponly=True,
        secure=False,  # True in production
        samesite='strict',
        max_age=3600
    )
    
    return response
```

---

## Summary Table

| Step | What | Why | Code |
|------|------|-----|------|
| 1 | Validate state | CSRF prevention | `state_store.validate()` |
| 2 | Exchange code | Get tokens from Google | `POST /token` |
| 3 | Decode ID token | Extract user info | `jwt.decode()` |
| 4 | Find/create user | User registration | `db.find_or_create()` |
| 5 | Issue JWT | Your own token | `jwt.encode()` |
| 6 | Set cookie | HTTP only | `response.set_cookie()` |

---

## Key Takeaways

✅ State prevents CSRF attacks (single-use)  
✅ Code exchange must happen on backend (uses client_secret)  
✅ Decode ID token (don't call /userinfo)  
✅ Issue your own JWT (not Google's token)  
✅ Use httpOnly cookies (prevent XSS)  
✅ Test error cases (expired code, wrong state, etc.)  

---

That's Day 12! 🎉
