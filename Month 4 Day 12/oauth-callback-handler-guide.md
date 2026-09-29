# Day 12: OAuth Callback Handler — Complete Guide
## Exchange Code for Token & Create User

---

## 🎯 What Happens Today

After user authorizes on Google's consent screen, they're redirected back to YOUR app with an authorization code.

**This route handles the callback:**
```python
@app.get('/auth/google/callback')
async def google_callback(code: str, state: str, request: Request):
    """Handle Google's redirect back to our app"""
    # Step 1: Validate state (CSRF protection)
    # Step 2: Exchange code for Google access token
    # Step 3: Fetch user profile from Google
    # Step 4: Find or create user in database
    # Step 5: Issue our own JWT token
    # Step 6: Return user to dashboard
```

---

## Part 1: The Complete Flow Diagram

```
Google                              Your App
  │                                   │
  ├─ User authorizes                  │
  │                                   │
  └─ Redirect with code ─────────────→│
                                      │
                                 CALLBACK HANDLER
                                      │
     ┌─────────────────────────────┬──┴──┬────────────────────┐
     │                             │     │                    │
     │                          Step 1  Step 2              Step 3
     │                          Validate Exchange Code      Fetch
     │                          State   for Token          Profile
     │                             │     │                    │
     │                          CSRF    HTTP POST to       HTTP GET to
     │                          Check   Google Token       Google
     │                                  Endpoint            UserInfo
     │                             │     │                    │
     │                         ✓ Valid  ✓ Tokens         ✓ User Data
     │                             │     │                    │
     │◄─────────────────────────────────────────────────────┤
     │                             │  Step 4  Step 5      Step 6
     │                             │  Find or Create    Issue JWT
     │                             │  User in DB        Set Cookie
     │                          ┌─────────────────────┐
     │                          │  Database           │
     │                          │  ┌───────────────┐  │
     │                          │  │ Users Table   │  │
     │                          │  │ ┌───────────┐ │  │
     │                          │  │ │ email     │ │  │
     │                          │  │ │ google_id │ │  │
     │                          │  │ │ name      │ │  │
     │                          │  │ │ picture   │ │  │
     │                          │  │ └───────────┘ │  │
     │                          │  └───────────────┘  │
     │                          └─────────────────────┘
     │                             │
     │                          ✓ User found/created
     │                          ✓ JWT issued
     │                          ✓ Session cookie set
     │
  ✓ Redirect to /dashboard
  ✓ User logged in!
```

---

## Part 2: Step 1 — Validate State (CSRF Protection)

### What State Does
State prevents CSRF (Cross-Site Request Forgery) attacks.

**Attack scenario without state:**
```
1. Attacker tricks user into clicking malicious link
2. Link initiates Google OAuth flow (attacker's account)
3. User is redirected to Google
4. Google asks: "Do you want to authorize attacker's app?"
5. User clicks "Yes" (confused)
6. User is now logged into attacker's account in attacker's app
```

**How state prevents this:**
```
1. Your app generates random state before redirecting
2. State is stored securely (httpOnly cookie or session)
3. User is redirected to Google WITH state
4. Google includes state in redirect back
5. Your app verifies: does returned state match stored state?
6. Only if they match, proceed with token exchange
7. Attacker can't match state, attack fails
```

### Implementation

```python
@app.get('/auth/google/callback')
async def google_callback(
    code: str,
    state: str,
    request: Request
):
    """STEP 1: Validate state (CSRF protection)"""
    
    # Get state from secure httpOnly cookie
    cookie_state = request.cookies.get('oauth_state')
    
    # Verify state exists
    if not cookie_state:
        raise HTTPException(
            status_code=400,
            detail='State cookie missing (CSRF attack?)'
        )
    
    # Verify state in callback matches state we set
    if cookie_state != state:
        raise HTTPException(
            status_code=400,
            detail='State mismatch (CSRF attack detected!)'
        )
    
    # Verify state isn't expired
    # (State should be validated server-side with timestamp)
    if not state_store.validate(cookie_state):
        raise HTTPException(
            status_code=400,
            detail='State expired (possible CSRF attack)'
        )
    
    print(f'✓ State validated: {state[:20]}...')
    
    # Continue to next step...
```

### State Validation Best Practices

```python
class StateStore:
    def validate(self, state: str) -> bool:
        """Validate state"""
        if state not in self.states:
            return False
        
        state_data = self.states[state]
        
        # Check expiration (10 minutes)
        if datetime.now() - state_data['created_at'] > timedelta(minutes=10):
            return False
        
        # Check if already used (prevent replay)
        if state_data['used']:
            return False
        
        # Mark as used
        state_data['used'] = True
        return True
```

**Why mark as used?**
- Prevents replay attacks (can't use same state twice)
- Each authorization must have unique state
- Once used, can't be reused

---

## Part 3: Step 2 — Exchange Code for Token

### What Happens
Your backend makes a POST request to Google's token endpoint, exchanging the authorization code for an access token.

**CRITICAL:** This request includes `client_secret`, which must NEVER be exposed to the browser. It must happen backend-to-backend.

### Implementation

```python
@app.get('/auth/google/callback')
async def google_callback(code: str, state: str, request: Request):
    # ... Step 1: Validate state ...
    
    """STEP 2: Exchange code for Google access token"""
    
    # Prepare token exchange request
    token_request = {
        'client_id': Config.GOOGLE_CLIENT_ID,
        'client_secret': Config.GOOGLE_CLIENT_SECRET,  # NEVER in browser!
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': Config.GOOGLE_REDIRECT_URI
    }
    
    # Make POST request to Google
    async with httpx.AsyncClient() as client:
        response = await client.post(
            Config.GOOGLE_TOKEN_URL,
            data=token_request,
            timeout=10.0
        )
    
    # Check for errors
    if response.status_code != 200:
        error_data = response.json()
        error_msg = error_data.get('error', 'unknown_error')
        raise HTTPException(
            status_code=400,
            detail=f'Token exchange failed: {error_msg}'
        )
    
    # Parse response
    token_response = response.json()
    
    print(f'✓ Code exchanged for token')
    print(f'  Access token: {token_response["access_token"][:20]}...')
    print(f'  Expires in: {token_response["expires_in"]} seconds')
    
    # Extract tokens
    access_token = token_response['access_token']
    id_token = token_response.get('id_token')
    refresh_token = token_response.get('refresh_token')
    expires_in = token_response['expires_in']
    
    # Continue to next step...
```

### Token Response Structure

```json
{
  "access_token": "ya29.a0AfH6SMBu...",
  "expires_in": 3599,
  "refresh_token": "1//0g...",
  "scope": "openid email profile",
  "token_type": "Bearer",
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

### What Each Token Does

| Token | Purpose | Lifetime | Revocation |
|-------|---------|----------|------------|
| `access_token` | Call Google APIs on user's behalf | ~1 hour | Can be revoked by Google |
| `refresh_token` | Get new access_token when expired | ~7 days | Can be revoked by Google |
| `id_token` | JWT with user info (OIDC) | ~1 hour | N/A (stateless) |

### Error Cases to Handle

```python
async def exchange_code_for_token(code: str):
    """Exchange code, handle all error cases"""
    
    token_request = {...}
    
    try:
        response = await client.post(
            Config.GOOGLE_TOKEN_URL,
            data=token_request,
            timeout=10.0
        )
    except httpx.TimeoutException:
        # Network timeout
        raise HTTPException(
            status_code=503,
            detail='Google token service timeout'
        )
    except httpx.NetworkError:
        # Network error
        raise HTTPException(
            status_code=503,
            detail='Google token service unreachable'
        )
    
    if response.status_code == 400:
        error = response.json()['error']
        if error == 'invalid_grant':
            # Code expired or already used
            raise HTTPException(
                status_code=400,
                detail='Authorization code expired or invalid'
            )
        elif error == 'invalid_code':
            # Code doesn't exist
            raise HTTPException(
                status_code=400,
                detail='Invalid authorization code'
            )
    
    if response.status_code == 401:
        # Client authentication failed (wrong secret)
        raise HTTPException(
            status_code=401,
            detail='Client authentication failed (check credentials)'
        )
    
    if response.status_code >= 500:
        # Google server error
        raise HTTPException(
            status_code=503,
            detail='Google service error'
        )
    
    return response.json()
```

---

## Part 4: Step 3 — Fetch User Profile

### Two Options

**Option A: Decode ID Token (Recommended for OIDC)**
```python
# ID token is a JWT containing user info
import jwt

id_token = token_response['id_token']

# Decode (without verification for simplicity)
# In production, verify signature
user_info = jwt.decode(
    id_token,
    options={'verify_signature': False}
)

# Extract user data
google_id = user_info['sub']
email = user_info['email']
name = user_info['name']
picture = user_info['picture']
email_verified = user_info['email_verified']
```

**Option B: Call UserInfo Endpoint (Extra API call)**
```python
# Call Google's userinfo endpoint
headers = {
    'Authorization': f'Bearer {access_token}'
}

async with httpx.AsyncClient() as client:
    response = await client.get(
        'https://www.googleapis.com/oauth2/v1/userinfo',
        headers=headers,
        timeout=10.0
    )

user_info = response.json()

# Response structure:
{
    'id': '1234567890',
    'email': 'user@example.com',
    'name': 'Alice Smith',
    'picture': 'https://lh3.googleusercontent.com/...',
    'email_verified': True
}
```

### Full Implementation (Decode ID Token)

```python
@app.get('/auth/google/callback')
async def google_callback(code: str, state: str, request: Request):
    # ... Step 1: Validate state ...
    # ... Step 2: Exchange code ...
    
    """STEP 3: Extract user info from ID token"""
    
    id_token = token_response['id_token']
    
    # Decode JWT (ID token)
    try:
        user_info = jwt.decode(
            id_token,
            options={'verify_signature': False}  # OK for demo
            # In production: verify signature using Google's public key
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=400,
            detail='Invalid ID token'
        )
    
    # Extract user info
    google_id = user_info.get('sub')  # Subject (unique user ID)
    email = user_info.get('email')
    name = user_info.get('name', '')
    picture = user_info.get('picture')
    email_verified = user_info.get('email_verified', False)
    
    # Validate required fields
    if not google_id or not email:
        raise HTTPException(
            status_code=400,
            detail='Invalid user info from Google'
        )
    
    print(f'✓ User info extracted from ID token')
    print(f'  Google ID: {google_id}')
    print(f'  Email: {email}')
    print(f'  Name: {name}')
    print(f'  Email verified: {email_verified}')
    
    # Continue to next step...
```

---

## Part 5: Step 4 — Find or Create User

### Find-or-Create Pattern

```python
@app.get('/auth/google/callback')
async def google_callback(code: str, state: str, request: Request):
    # ... Previous steps ...
    
    """STEP 4: Find or create user in database"""
    
    # Try to find existing user by Google ID
    user = user_db.find_by_google_id(google_id)
    
    if user:
        # Existing user - update last login
        user_db.update_last_login(user.id)
        print(f'✓ Returning user found: {email}')
    else:
        # New user - create in database
        user = user_db.create_user(
            google_id=google_id,
            email=email,
            name=name,
            picture=picture,
            email_verified=email_verified
        )
        print(f'✓ New user created: {email}')
    
    # Now we have a user object
    # Continue to next step...
```

### Database Schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    picture VARCHAR(2048),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    
    INDEX (google_id),
    INDEX (email)
);
```

### Find-or-Create Implementation

```python
class UserDatabase:
    def find_by_google_id(self, google_id: str) -> Optional[User]:
        """Find user by Google ID"""
        # For mock DB (in-memory)
        for user in self.users.values():
            if user.google_id == google_id:
                return user
        return None
    
    def create_user(
        self,
        google_id: str,
        email: str,
        name: str,
        picture: Optional[str] = None,
        email_verified: bool = False
    ) -> User:
        """Create new user from Google profile"""
        user = User(
            id=str(uuid.uuid4()),
            google_id=google_id,
            email=email,
            name=name,
            picture=picture,
            email_verified=email_verified,
            created_at=datetime.now().isoformat(),
            last_login=datetime.now().isoformat()
        )
        self.users[user.id] = user
        return user
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        if user_id in self.users:
            self.users[user_id].last_login = datetime.now().isoformat()
```

---

## Part 6: Step 5 — Issue Your Own JWT

### Why Your Own JWT?

**Don't store Google's access token long-term:**
```
❌ WRONG: Store Google's access_token in session/cookie
  - Google can revoke it without your knowledge
  - Doesn't represent permission to your app
  - Expires (refresh_token adds complexity)
  - Ties you to Google's token format

✅ RIGHT: Issue your own JWT
  - Represents permission to your app
  - You control expiration
  - Works even if Google is down
  - Your own token format
  - Google's token is temporary (only for callback)
```

### JWT Structure

```python
# Payload (what's inside the JWT)
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",  # YOUR user ID
  "email": "user@example.com",
  "name": "Alice Smith",
  "picture": "https://...",
  "iat": 1516239022,  # Issued at (now)
  "exp": 1516242622  # Expires in 1 hour
}

# Headers
{
  "alg": "HS256",  # Algorithm
  "typ": "JWT"     # Type
}

# Signature
# HMAC-SHA256(
#   base64url(header) + "." + base64url(payload),
#   secret
# )
```

### Implementation

```python
@app.get('/auth/google/callback')
async def google_callback(code: str, state: str, request: Request):
    # ... Previous steps get us a user object ...
    
    """STEP 5: Issue your own JWT token"""
    
    # Create JWT payload
    now = datetime.utcnow()
    payload = {
        'user_id': user.id,
        'email': user.email,
        'name': user.name,
        'picture': user.picture,
        'iat': now,
        'exp': now + timedelta(hours=24)  # Expires in 24 hours
    }
    
    # Sign JWT with your secret
    jwt_token = jwt.encode(
        payload,
        Config.JWT_SECRET,
        algorithm='HS256'
    )
    
    print(f'✓ JWT issued: {jwt_token[:50]}...')
    
    # Continue to next step...
```

### Why Not Use Google's Token?

**Google's access_token:**
```
Pros:
  - Proves user authorized on Google

Cons:
  - Expires (usually ~1 hour)
  - Refresh token needed (adds complexity)
  - Only works for Google APIs
  - Can be revoked by Google
  - Ties your auth to Google's infrastructure
  - Can't use it for your other microservices
```

**Your own JWT:**
```
Pros:
  - Represents permission to YOUR app
  - You control expiration
  - Works for your other services
  - Doesn't depend on Google
  - Stateless (can validate without DB)
  - Standard format (industry standard)

Cons:
  - Need to sign/verify JWTs
  - Need to manage secret key
```

### Token Lifetime Strategy

```python
# Access token (your JWT)
Access_Token_Lifetime = timedelta(hours=1)  # 1 hour
# Short-lived, can be used for API calls

# Refresh token (in cookie)
Refresh_Token_Lifetime = timedelta(days=7)  # 7 days
# Long-lived, used to get new access token when expired

# Google's token (not stored)
# Thrown away after callback
# Only used to get user info on callback
```

---

## Part 7: Step 6 — Return to Dashboard

### Complete Callback Handler

```python
@app.get('/auth/google/callback')
async def google_callback(
    code: str,
    state: str,
    request: Request,
    response: Response
):
    """Complete OAuth callback handler"""
    
    # STEP 1: Validate state
    cookie_state = request.cookies.get('oauth_state')
    if not cookie_state or cookie_state != state:
        raise HTTPException(status_code=400, detail='CSRF check failed')
    
    if not state_store.validate(cookie_state):
        raise HTTPException(status_code=400, detail='State expired/invalid')
    
    # STEP 2: Exchange code for token
    token_response = await exchange_code_for_token(code)
    
    # STEP 3: Get user info from ID token
    user_info = jwt.decode(
        token_response['id_token'],
        options={'verify_signature': False}
    )
    
    # STEP 4: Find or create user
    user = user_db.find_by_google_id(user_info['sub'])
    if not user:
        user = user_db.create_user(
            google_id=user_info['sub'],
            email=user_info['email'],
            name=user_info.get('name', ''),
            picture=user_info.get('picture')
        )
    else:
        user_db.update_last_login(user.id)
    
    # STEP 5: Issue our own JWT
    now = datetime.utcnow()
    jwt_payload = {
        'user_id': user.id,
        'email': user.email,
        'name': user.name,
        'iat': now,
        'exp': now + timedelta(hours=24)
    }
    
    jwt_token = jwt.encode(
        jwt_payload,
        Config.JWT_SECRET,
        algorithm='HS256'
    )
    
    # STEP 6: Set cookie and redirect
    response = RedirectResponse(url='/dashboard', status_code=302)
    
    response.set_cookie(
        'access_token',
        jwt_token,
        max_age=3600,  # 1 hour
        httponly=True,
        secure=True,  # HTTPS only
        samesite='strict'
    )
    
    # Clean up
    response.delete_cookie('oauth_state')
    
    return response
```

---

## Part 8: Security Considerations

### Secure Cookie Settings

```python
response.set_cookie(
    'access_token',
    jwt_token,
    # Security options
    httponly=True,      # ✓ Prevent XSS (JS can't access)
    secure=True,        # ✓ HTTPS only (no HTTP)
    samesite='strict',  # ✓ CSRF protection (SameSite)
    # Expiration
    max_age=3600,       # ✓ 1 hour (short-lived)
    # Path
    path='/',           # ✓ Available to entire app
)
```

### What Each Setting Does

| Setting | Why It Matters | Value |
|---------|---|---|
| `httponly=True` | Prevents XSS attacks (JS can't steal token) | Always True |
| `secure=True` | HTTPS only (not sent over HTTP) | True in production, False for localhost |
| `samesite='strict'` | CSRF protection (cookie not sent cross-origin) | 'strict' or 'lax' |
| `max_age` | Token lifetime (when cookie expires) | 3600 (1 hour) |
| `path='/'` | Where cookie is sent | '/' (entire app) |

### Token Revocation

```python
# How to revoke tokens (logout)

class TokenBlacklist:
    """Track revoked tokens"""
    
    def __init__(self):
        self.blacklisted = set()
    
    def revoke(self, token: str):
        """Add token to blacklist"""
        payload = jwt.decode(token, Config.JWT_SECRET)
        self.blacklisted.add(token)
        
    def is_blacklisted(self, token: str) -> bool:
        """Check if token is revoked"""
        return token in self.blacklisted

# On logout
blacklist.revoke(token)
response.delete_cookie('access_token')
```

---

## Part 9: Error Handling

### Handle All Error Cases

```python
async def google_callback(code: str, state: str):
    """Error handling for callback"""
    
    # CSRF attack
    if state_mismatch:
        log_security_event('CSRF_ATTEMPT', {'state': state})
        raise HTTPException(status_code=400, detail='CSRF detected')
    
    # Code expired
    try:
        tokens = await exchange_code_for_token(code)
    except HTTPException as e:
        if 'invalid_grant' in str(e):
            log_security_event('EXPIRED_CODE', {'code': code[:10]})
            raise HTTPException(
                status_code=400,
                detail='Code expired. Please login again.'
            )
    
    # Invalid user data
    if not user_info.get('email'):
        log_security_event('MISSING_EMAIL', {'user_info': user_info})
        raise HTTPException(status_code=400, detail='Email required')
    
    # Database error
    try:
        user = user_db.find_or_create_user(user_info)
    except DatabaseError:
        log_error('DATABASE_ERROR', {'user_info': user_info})
        raise HTTPException(
            status_code=500,
            detail='Database error. Please try again.'
        )
    
    # JWT signing error
    try:
        jwt_token = jwt.encode(payload, Config.JWT_SECRET)
    except Exception as e:
        log_error('JWT_ERROR', {'error': str(e)})
        raise HTTPException(status_code=500, detail='Token generation failed')
```

---

## Part 10: Testing the Callback

### Manual Testing

```bash
# 1. Start app
python oauth2-google-implementation.py

# 2. Visit login page
http://localhost:8000/auth/google/login

# 3. You'll be redirected to Google
# 4. Log in with your Google account
# 5. Click [Allow] on consent screen
# 6. You'll be redirected to callback with:
#    http://localhost:8000/auth/google/callback?code=...&state=...

# 7. App will:
#    - Validate state
#    - Exchange code for token
#    - Get user info
#    - Create/find user
#    - Issue JWT
#    - Set cookie
#    - Redirect to /dashboard

# 8. You'll see your profile!
```

### Unit Tests

```python
def test_validate_state():
    """State validation prevents CSRF"""
    store = StateStore()
    state = store.generate()
    
    # Valid state
    assert store.validate(state) == True
    
    # Can't use twice (replay protection)
    assert store.validate(state) == False

def test_exchange_code_for_token():
    """Code exchange returns valid tokens"""
    # Mock Google's token endpoint
    mock_response = {
        'access_token': 'ya29.a0AfH6SMBu...',
        'id_token': 'eyJhbGc...',
        'expires_in': 3599
    }
    
    # Test exchange
    tokens = exchange_code_for_token('valid_code')
    assert tokens['access_token']
    assert tokens['id_token']

def test_decode_id_token():
    """ID token decoding extracts user info"""
    payload = {
        'sub': '123456',
        'email': 'user@example.com',
        'name': 'Alice'
    }
    
    id_token = jwt.encode(payload, 'secret')
    decoded = jwt.decode(id_token, options={'verify_signature': False})
    
    assert decoded['email'] == 'user@example.com'
    assert decoded['sub'] == '123456'

def test_find_or_create_user():
    """User is created on first login"""
    user_info = {
        'sub': '123456',
        'email': 'user@example.com',
        'name': 'Alice'
    }
    
    # First call creates
    user1 = user_db.find_or_create_user(user_info)
    assert user1.email == 'user@example.com'
    
    # Second call finds
    user2 = user_db.find_or_create_user(user_info)
    assert user1.id == user2.id  # Same user

def test_jwt_token_creation():
    """JWT token is valid and expires correctly"""
    payload = {
        'user_id': 'abc123',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    
    token = jwt.encode(payload, 'secret', algorithm='HS256')
    decoded = jwt.decode(token, 'secret', algorithms=['HS256'])
    
    assert decoded['user_id'] == 'abc123'
```

---

## Summary: The 6 Steps of Callback Handling

| Step | Action | Security |
|------|--------|----------|
| 1 | Validate state | CSRF protection (single-use) |
| 2 | Exchange code | Uses client_secret (backend only) |
| 3 | Get user info | From JWT (no extra API call) |
| 4 | Find/create user | Register on first login |
| 5 | Issue JWT | Your own token (not Google's) |
| 6 | Set cookie | httpOnly, secure, short-lived |

**Remember:** Don't store Google's access token. Issue your own JWT instead.

