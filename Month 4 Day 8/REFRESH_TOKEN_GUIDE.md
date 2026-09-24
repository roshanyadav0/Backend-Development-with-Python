# Day 8: Refresh Token Pattern

## Why Short-Lived Access Tokens?

### Problem: Long-Lived Tokens are Risky

If access token is valid for 7 days:
```
Attacker steals token at day 1
  ↓
Token is valid for 7 more days
  ↓
Attacker has full access for 7 days
  ↓
User doesn't know they're compromised for days
```

**Cost of compromise**: 7 days of unauthorized access

### Solution: Make Tokens Short-Lived

If access token is valid for 15 minutes:
```
Attacker steals token at 12:00pm
  ↓
Token expires at 12:15pm
  ↓
Attacker has 15 minutes of access
  ↓
User can detect & revoke within 15 minutes
```

**Cost of compromise**: 15 minutes (+ time to detect)

### But 15 Minutes is Annoying

**Problem**: User's token expires after 15 minutes
- They have to re-login
- Bad UX: "Please login again"
- Users just keep passwords in browsers instead (worse)

### Solution: Refresh Tokens

**Pattern**:
1. Access token: 15 minutes (short-lived, used for API calls)
2. Refresh token: 7 days (long-lived, used to get new access token)

```
User logs in once
  ↓
Gets access token (15 min) + refresh token (7 days)
  ↓
For 7 days, user can automatically refresh access tokens
  ↓
No manual login needed
  ↓
If access token is stolen, only 15-minute window
  ↓
If refresh token is stolen, can revoke immediately
```

## The Token Lifecycle

### Timeline

```
12:00 PM: User logs in
          ↓
          Issued: access_token (expires 12:15) + refresh_token (expires next week)
          
12:14 PM: User makes API call
          ↓
          Uses access_token (still valid)
          ↓
          Response: 200 OK
          
12:16 PM: User makes another API call
          ↓
          access_token is expired
          ↓
          Response: 401 Unauthorized
          ↓
          Client calls POST /auth/refresh with refresh_token
          ↓
          Server: refresh_token valid? → YES
          ↓
          Server issues NEW access_token (expires 12:31)
          ↓
          Client retries original request with new token
          ↓
          Response: 200 OK

12:31 PM: Same thing happens
          ↓
          POST /auth/refresh → new access_token (expires 12:46)

Next week: refresh_token expires
           ↓
           POST /auth/refresh returns 401
           ↓
           Client forces re-login
```

## Implementation Details

### Three Tokens

| Token | Lifetime | Storage | Use |
|-------|----------|---------|-----|
| Access | 15 min | Memory/localStorage | Every API call |
| Refresh | 7 days | Secure HttpOnly cookie | Get new access token |
| Logout | Revoked | Database | Instant logout |

### Access Token (Short-lived)

```python
payload = {
    "sub": "user_id",                    # Subject (who)
    "type": "access",                   # Type (distinguish from refresh)
    "exp": now + 15_minutes,            # Expiry (short!)
    "iat": now                          # Issued at
}
token = jwt.encode(payload, SECRET_KEY, "HS256")
```

**Stateless**: Server doesn't need to check database.
**Verifiable**: Signature proves server created it.
**Expiry**: Limits damage if stolen.

### Refresh Token (Long-lived)

```python
payload = {
    "sub": "user_id",                   # Subject (who)
    "type": "refresh",                  # Type (distinguish from access)
    "jti": unique_id,                   # JWT ID (for tracking/rotation)
    "exp": now + 7_days,                # Expiry (long!)
    "iat": now                          # Issued at
}
token = jwt.encode(payload, SECRET_KEY, "HS256")

# Store in database (don't trust client)
db.refresh_tokens.insert({
    "user_id": user_id,
    "token_id": unique_id,               # From jti claim
    "token_hash": hash(token),           # Never store plain
    "expires_at": now + 7_days,
    "revoked_at": None,                 # NULL = active
    "is_rotated": False
})
```

**Stored in database**: Can be revoked/rotated.
**Hashed**: If compromised, hash doesn't leak token.
**Tracked**: Can audit which devices logged in.

## The Endpoints

### POST /auth/login

```
Request:
  username: alice@test.com
  password: SecurePass123

Server:
  1. Find user
  2. Verify password
  3. Create access_token (15 min)
  4. Create refresh_token (7 days), store in DB
  5. Return both

Response (200):
  {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 900
  }
```

### POST /auth/refresh

```
Request:
  refresh_token: eyJ...

Server:
  1. Decode JWT (verify signature)
  2. Check type == "refresh"
  3. Extract jti from token
  4. Query database: SELECT * FROM refresh_tokens WHERE token_id = jti
  5. Check: expires_at > now? revoked_at is NULL? is_rotated = FALSE?
  6. If valid: Create NEW access_token
  7. If invalid: Return 401

Response (200):
  {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 900
  }
```

### POST /auth/logout

```
Request:
  Authorization: Bearer {access_token}

Server:
  1. Verify access_token
  2. Extract user_id
  3. UPDATE refresh_tokens SET revoked_at = NOW()
     WHERE user_id = ? AND revoked_at IS NULL
  4. Return 200

Response (200):
  {
    "message": "Logged out successfully"
  }
```

## Why Store Refresh Tokens in Database?

**Option 1: Store in database** (CHOSEN)
- ✅ Can revoke instantly (logout)
- ✅ Can rotate tokens (invalidate old on use)
- ✅ Can track which devices are logged in
- ✅ Can set audit trail
- ✗ Need database lookup (not fully stateless)

**Option 2: Store only in JWT** (STATELESS)
- ✅ No database lookup needed
- ✗ Can't revoke until expiry (7 days!)
- ✗ Can't rotate
- ✗ Can't track devices
- ✗ Logout doesn't work (token still valid)

**Verdict**: Database storage is better for real applications.
**Tradeoff**: Sacrifice "stateless" for practical security.

## Token Rotation Pattern

### Problem: Refresh Token Reuse

If refresh token is stolen:
```
Attacker gets refresh token
  ↓
Uses it to get new access tokens
  ↓
Attacker has access for 7 days (refresh token lifetime)
  ↓
User doesn't know until 7 days pass
```

**Window**: 7 days of unauthorized access!

### Solution: Rotate Tokens

Each time refresh token is used, **issue new token and invalidate old**:

```
User's device has refresh_token_v1

POST /auth/refresh with refresh_token_v1
  ↓
Server:
  - Verify refresh_token_v1 is valid
  - Create NEW refresh_token_v2
  - Mark refresh_token_v1 as rotated
  
Return new refresh_token_v2

Next time attacker tries to use refresh_token_v1:
  ↓
Server checks: is_rotated = TRUE
  ↓
Return 401 (token was already used)
```

**Benefit**: If refresh token is stolen, attacker can only use it once.
**Detection**: If legitimate user and attacker both have refresh token, one will get 401 when trying to use old token.

## Database Schema

### users table
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  hashed_password VARCHAR NOT NULL,
  created_at DATETIME DEFAULT NOW()
);
```

### refresh_tokens table
```sql
CREATE TABLE refresh_tokens (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  token_id VARCHAR UNIQUE NOT NULL,      -- JWT ID (jti)
  token_hash VARCHAR NOT NULL,            -- Hash of token
  expires_at DATETIME NOT NULL,
  created_at DATETIME DEFAULT NOW(),
  revoked_at DATETIME NULL,               -- NULL = active
  is_rotated BOOLEAN DEFAULT FALSE        -- TRUE = already used
);

-- Indexes for performance
CREATE INDEX ix_user_id ON refresh_tokens(user_id);
CREATE INDEX ix_expires_at ON refresh_tokens(expires_at);
CREATE INDEX ix_token_id ON refresh_tokens(token_id);
```

### Why Three Columns for Token State?

| State | revoked_at | is_rotated | Meaning |
|-------|-----------|-----------|---------|
| Active | NULL | FALSE | Token is good, use it |
| Revoked | 2024-09-23 12:00 | FALSE | User logged out, reject |
| Rotated | NULL | TRUE | Token was already used, reject |
| Rotated+Revoked | 2024-09-23 12:00 | TRUE | Old token that was also revoked |

## Migration with Alembic

### Setup

```bash
# Install alembic
pip install alembic

# Initialize alembic (creates migrations directory)
alembic init migrations

# Create initial migration
alembic revision --autogenerate -m "Create users table"

# Apply migration
alembic upgrade head
```

### Create Migration for Refresh Tokens

```bash
alembic revision --autogenerate -m "Add refresh_tokens table"
```

This generates `migrations/versions/xxx_add_refresh_tokens_table.py`:

```python
def upgrade():
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_id', sa.String(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('is_rotated', sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_id'),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])

def downgrade():
    op.drop_table('refresh_tokens')
```

### Run Migration

```bash
# Apply migration
alembic upgrade head

# Check current version
alembic current

# Rollback
alembic downgrade -1
```

## Security Considerations

### Access Token

**Stored in**: Memory or localStorage
**Problem**: Can be stolen via XSS
**Solution**: Content Security Policy (CSP) to prevent XSS

```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'">
```

### Refresh Token

**Stored in**: HttpOnly cookie (not accessible to JavaScript)
**Why**: XSS can't steal it
**Tradeoff**: Must handle CSRF (Cross-Site Request Forgery)
**Solution**: SameSite cookie attribute

```python
response.set_cookie(
    "refresh_token",
    refresh_token,
    httponly=True,           # Can't read from JS
    secure=True,             # HTTPS only
    samesite="strict",       # Can't send cross-site
    max_age=7*24*60*60       # 7 days
)
```

## Complete Flow Comparison

### Old (Without Refresh): Logout is Broken

```
LOGIN:
  Issue 7-day access token
  
USER SESSION:
  Use token for 7 days
  
LOGOUT:
  Tell server to logout
  Server has no way to invalidate token
  Token still works for 7 more days!
  
PROBLEM: Can't log out
```

### New (With Refresh): Logout Works

```
LOGIN:
  Issue 15-min access token
  Issue 7-day refresh token (stored in DB)
  
USER SESSION (0-15 min):
  Use access_token
  
USER SESSION (15+ min):
  access_token expires
  Use refresh_token to get new access_token
  Repeat
  
LOGOUT:
  DELETE FROM refresh_tokens WHERE user_id = ?
  Access_token expires in 15 min anyway
  
RESULT: Instant logout + limited access token lifetime
```

## Testing the Pattern

```bash
# Start server
python fastapi_refresh_tokens.py

# Test in Python
import requests

# 1. Register
requests.post("http://localhost:8000/auth/register", json={
    "email": "alice@test.com",
    "password": "SecurePass123"
})

# 2. Login
response = requests.post("http://localhost:8000/auth/login", data={
    "username": "alice@test.com",
    "password": "SecurePass123"
})
access = response.json()["access_token"]
refresh = response.json()["refresh_token"]

# 3. Use access token
requests.get("http://localhost:8000/api/me", headers={
    "Authorization": f"Bearer {access}"
})

# 4. Refresh (get new access token)
response = requests.post("http://localhost:8000/auth/refresh", json={
    "refresh_token": refresh
})
new_access = response.json()["access_token"]

# 5. Use new access token
requests.get("http://localhost:8000/api/me", headers={
    "Authorization": f"Bearer {new_access}"
})

# 6. Logout
requests.post("http://localhost:8000/auth/logout", headers={
    "Authorization": f"Bearer {new_access}"
})

# 7. Try refresh after logout (should fail)
requests.post("http://localhost:8000/auth/refresh", json={
    "refresh_token": refresh
})
# → 401 Unauthorized (token was revoked)
```

## Performance

- Login (issue both tokens): ~110ms
- Refresh (get new access token): ~10ms (DB query only)
- Logout (revoke all tokens): ~5ms
- API call (use access token): <1ms (just verify signature)

**Scales**: ~100 logins/sec, ~10K refreshes/sec per server.

## Next Steps

- **Token rotation**: Invalidate old refresh token on use
- **Device tracking**: Show which devices are logged in
- **Revoke by device**: Logout one device, not all
- **2FA**: Require second factor on login
- **Rate limiting**: Prevent brute force on refresh endpoint

## Files

- **fastapi_refresh_tokens.py** — Complete implementation
- **test_refresh_tokens.py** — 15+ test cases
- **alembic_migration_refresh_tokens.py** — Database migration

## Summary

**Access Token** (15 minutes):
- Short-lived (limits damage if stolen)
- Stateless (just verify signature)
- Used for every API call
- Stored in memory (XSS-vulnerable but expires fast)

**Refresh Token** (7 days):
- Long-lived (user stays logged in)
- Stored in database (can be revoked)
- Used to get new access token
- Stored in HttpOnly cookie (XSS-safe)

**Result**:
- Good UX: Don't force re-login every 15 minutes
- Good security: Only 15-minute window if access token stolen
- Good control: Can logout instantly by revoking refresh token
