# Week 1 Review: Deep Dive on JWT Security

## Question 1: What Happens if Someone Intercepts a JWT?

### Scenario: Attacker steals JWT from network

**If HTTPS is used (CORRECT):**
```
Client → HTTPS → Server
  Attacker can't see traffic (encrypted)
  Even if intercepted, encrypted data is useless
  ✓ JWT is safe in transit
```

**If HTTP is used (WRONG):**
```
Client → HTTP → Server
  Attacker intercepts: GET /api/me
         Authorization: Bearer eyJhbGciOiJIUzI1NiI...
  
  Attacker now has the token.
  Attacker can use it to:
    ✗ GET /api/me → see user data
    ✗ POST /api/update → modify user data
    ✗ DELETE /api/account → delete account
  
  Token is valid for 15 minutes → 15 minutes of access.
```

### Scenario: Attacker modifies JWT

```
Original token (valid):
  eyJhbGciOiJIUzI1NiI...{sub: "user_1", role: "user"}...xyz123

Attacker tries to change role:
  eyJhbGciOiJIUzI1NiI...{sub: "user_1", role: "admin"}...xyz123
  
  Server decodes and verifies signature:
    HMAC(SECRET_KEY, header.payload) == stored_signature?
  
  Signature doesn't match (attacker doesn't know SECRET_KEY)
  ✓ JWT is rejected with 401 Unauthorized
```

### Scenario: Attacker forges new JWT

```
Attacker knows user_id = 5, creates new JWT:
  payload = {sub: "5", exp: +15min}
  tries to sign: jwt.encode(payload, "wrong_secret", "HS256")
  
  But attacker doesn't have SECRET_KEY.
  Signature is invalid.
  
  Server verifies with real SECRET_KEY:
    HMAC(real_secret, header.payload) != attacker_signature
  
  ✓ JWT is rejected with 401 Unauthorized
```

### Scenario: Attacker steals JWT, uses it

```
Attacker steals token (e.g., via XSS, network eavesdropping):
  Token: eyJhbGciOiJIUzI1NiI...
  
  Attacker's request:
    GET /api/me
    Authorization: Bearer eyJhbGciOiJIUzI1NiI...
  
  Server verifies signature: ✓ Valid
  Server checks expiry: ✓ Not expired
  Server returns: {id: 1, email: user@example.com}
  
  ✗ Attacker can access user's data for 15 minutes
  ✓ After 15 minutes, token expires (attacker locked out)
```

### Scenario: Attacker changes token expiry

```
Original token:
  {sub: "user_1", exp: 1625000000}  (expires in 15 min)

Attacker modifies:
  {sub: "user_1", exp: 2000000000}  (expires in 10 years)

Server checks signature:
  payload_signature = HMAC(SECRET_KEY, header.modified_payload)
  stored_signature != payload_signature
  
  ✗ Token rejected
  ✓ Can't extend token lifetime without SECRET_KEY
```

## Summary: JWT Security Properties

| Threat | Outcome |
|--------|---------|
| Eavesdropping (HTTP) | ✗ Token stolen, usable for 15 min |
| Network encryption (HTTPS) | ✓ Token encrypted in transit |
| Modifying payload | ✓ Signature breaks, token rejected |
| Forging new token | ✓ Can't sign without SECRET_KEY |
| Using stolen token | ✗ Works until expiry (15 min window) |
| Extending expiry | ✓ Signature breaks, token rejected |

**Best practices:**
- ✅ Always use HTTPS (encrypt in transit)
- ✅ Keep SECRET_KEY secret (don't commit to git, use env vars)
- ✅ Short token lifetime (15 minutes, not hours/days)
- ✅ Refresh tokens for longer sessions (separate, secure storage)
- ✅ Store tokens securely on client (not localStorage if possible)

---

## Question 2: Test 5 Edge Cases

### Edge Case 1: Expired Token

**Scenario:** Token was issued 16 minutes ago, JWT exp is in the past.

```python
# Expired token
expired_payload = {
    "sub": "1",
    "exp": datetime.utcnow() - timedelta(minutes=1)  # Expired 1 min ago
}
expired_token = jwt.encode(expired_payload, SECRET_KEY, "HS256")

# Try to use it
headers = {"Authorization": f"Bearer {expired_token}"}
response = client.get("/api/me", headers=headers)

# Expected: 401 Unauthorized
assert response.status_code == 401
assert "expired" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()
```

**What happens:**
1. Client sends expired token
2. Server calls `jwt.decode(token, SECRET_KEY, ...)`
3. JWT library checks: `if exp < datetime.utcnow()`
4. Raises `ExpiredSignatureError` (subclass of `JWTError`)
5. `get_current_user()` catches it, returns 401

### Edge Case 2: Signature Tampered

**Scenario:** Attacker modifies token, changes last 10 characters.

```python
# Valid token
response = client.post("/auth/login", data={"username": "alice@test.com", "password": "Pass"})
valid_token = response.json()["access_token"]

# Attacker corrupts signature
tampered = valid_token[:-10] + "xxxxxxxxxx"

# Try to use it
headers = {"Authorization": f"Bearer {tampered}"}
response = client.get("/api/me", headers=headers)

# Expected: 401 Unauthorized
assert response.status_code == 401
```

**What happens:**
1. Client sends tampered token
2. Server calls `jwt.decode(token, SECRET_KEY, ...)`
3. JWT library verifies signature:
   ```python
   expected_sig = HMAC(SECRET_KEY, header.payload)
   if expected_sig != provided_sig: raise JWTError
   ```
4. Signatures don't match (attacker changed payload)
5. `get_current_user()` catches `JWTError`, returns 401

### Edge Case 3: Wrong Secret Key

**Scenario:** Token was signed with the wrong key.

```python
# Token signed with wrong secret
wrong_secret = "different-secret-key"
payload = {"sub": "1", "exp": datetime.utcnow() + timedelta(minutes=15)}
wrong_token = jwt.encode(payload, wrong_secret, "HS256")

# Try to use it
headers = {"Authorization": f"Bearer {wrong_token}"}
response = client.get("/api/me", headers=headers)

# Expected: 401 Unauthorized
assert response.status_code == 401
```

**What happens:**
1. Client sends token signed with wrong key
2. Server calls `jwt.decode(token, SECRET_KEY, ...)`
3. Server tries to verify signature with its own SECRET_KEY
4. Signature doesn't match (token signed with different key)
5. `JWTError` raised, caught in `get_current_user()`, returns 401

### Edge Case 4: Missing Required Claim

**Scenario:** JWT payload missing the `sub` (user_id) claim.

```python
# Token without sub claim
no_sub_payload = {"exp": datetime.utcnow() + timedelta(minutes=15)}
no_sub_token = jwt.encode(no_sub_payload, SECRET_KEY, "HS256")

# Try to use it
headers = {"Authorization": f"Bearer {no_sub_token}"}
response = client.get("/api/me", headers=headers)

# Expected: 401 Unauthorized
assert response.status_code == 401
```

**What happens:**
1. Client sends token without `sub` claim
2. Server calls `jwt.decode(token, SECRET_KEY, ...)`
3. Signature is valid (token wasn't tampered with)
4. Expiry is valid (token isn't expired)
5. But `payload.get("sub")` returns None
6. `get_current_user()` checks `if not user_id: raise HTTPException(401)`

### Edge Case 5: User Deleted After Login

**Scenario:** User logs in, gets token. Then admin deletes user. Token still tries to work.

```python
# User registers and logs in
client.post("/auth/register", json={"email": "alice@test.com", "password": "Pass123"})
login_response = client.post("/auth/login", data={"username": "alice@test.com", "password": "Pass123"})
token = login_response.json()["access_token"]

# In another thread, admin deletes the user from database
db.query(UserDB).filter(UserDB.email == "alice@test.com").delete()
db.commit()

# Try to use token
headers = {"Authorization": f"Bearer {token}"}
response = client.get("/api/me", headers=headers)

# Expected: 401 Unauthorized
assert response.status_code == 401
```

**What happens:**
1. Client sends valid token
2. Server calls `jwt.decode(token, SECRET_KEY, ...)`
3. Signature is valid, expiry is valid
4. Payload extracts user_id = 1
5. `get_current_user()` queries database: `SELECT * FROM users WHERE id = 1`
6. User not found (was deleted)
7. `get_current_user()` returns 401

**Note:** This is a database check, not a JWT check. The token is still valid, but the user is gone.

---

## Test Implementation

```python
def test_edge_cases(client):
    """Test all 5 edge cases"""
    
    # Register a user first
    client.post(
        "/auth/register",
        json={"email": "alice@test.com", "password": "SecurePass123"}
    )
    
    # Get a valid token
    login = client.post(
        "/auth/login",
        data={"username": "alice@test.com", "password": "SecurePass123"}
    )
    token = login.json()["access_token"]
    
    # ===== EDGE CASE 1: Expired Token =====
    print("\n1. Testing expired token...")
    from datetime import datetime, timedelta
    from jose import jwt
    
    expired_payload = {"sub": "999", "exp": datetime.utcnow() - timedelta(hours=1)}
    expired_token = jwt.encode(expired_payload, SECRET_KEY, "HS256")
    
    response = client.get("/api/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    print("   ✓ Expired token rejected (401)")
    
    # ===== EDGE CASE 2: Tampered Signature =====
    print("2. Testing tampered signature...")
    tampered = token[:-10] + "xxxxxxxxxx"
    
    response = client.get("/api/me", headers={"Authorization": f"Bearer {tampered}"})
    assert response.status_code == 401
    print("   ✓ Tampered token rejected (401)")
    
    # ===== EDGE CASE 3: Wrong Secret =====
    print("3. Testing token with wrong secret...")
    wrong_token = jwt.encode(
        {"sub": "1", "exp": datetime.utcnow() + timedelta(minutes=15)},
        "wrong-secret-key",
        "HS256"
    )
    
    response = client.get("/api/me", headers={"Authorization": f"Bearer {wrong_token}"})
    assert response.status_code == 401
    print("   ✓ Wrong secret rejected (401)")
    
    # ===== EDGE CASE 4: Missing Required Claim =====
    print("4. Testing token without sub claim...")
    no_sub_token = jwt.encode(
        {"exp": datetime.utcnow() + timedelta(minutes=15)},
        SECRET_KEY,
        "HS256"
    )
    
    response = client.get("/api/me", headers={"Authorization": f"Bearer {no_sub_token}"})
    assert response.status_code == 401
    print("   ✓ Missing claim rejected (401)")
    
    # ===== EDGE CASE 5: User Deleted =====
    print("5. Testing deleted user...")
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.email == "alice@test.com").first()
    db.delete(user)
    db.commit()
    db.close()
    
    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    print("   ✓ Deleted user rejected (401)")
    
    print("\n✓ All edge cases handled correctly!")
```

---

## Question 3: JWT Controversy & Tradeoffs

### The JWT Promise

When JWTs were introduced, the promise was:
- **Stateless**: No database lookup needed to verify token
- **Scalable**: Any server can verify without shared state
- **Simple**: Just decode, verify signature, done

This is great for microservices and distributed systems.

### The Reality Check

After years of real-world use, JWT adoption revealed tradeoffs:

#### 1. **Logout Problem**

**Stateful (Session) Approach:**
```python
# User clicks "Logout"
DELETE FROM sessions WHERE session_id = 'abc123'

# User tries to use deleted session
SELECT * FROM sessions WHERE session_id = 'abc123'
# → Not found, return 401
```

**Stateless (JWT) Approach:**
```python
# User clicks "Logout"
# What do we do? Token is still valid until expiry!
# Options:
#   1. Wait 15 minutes (bad UX)
#   2. Blacklist the token in database (defeats "stateless")
#   3. Add to cache, check on every request (defeats "stateless")
```

**Problem**: To truly log out with JWT, you need statefulness (a blacklist).
**Irony**: The feature that made JWT "stateless" requires database lookup for logout.

#### 2. **Immediate Permission Changes**

**Stateful Session:**
```python
# Admin revokes user's permission
UPDATE users SET permissions = '...' WHERE id = 123

# User immediately loses access
SELECT * FROM sessions WHERE session_id = 'xyz'
# → Find session, check permissions in database
# → Permissions revoked, return 403
```

**Stateless JWT:**
```python
# Admin revokes user's permission
UPDATE users SET permissions = '...' WHERE id = 123

# User still has access (token contains old permissions)
# Token valid for 10 more minutes

# Options:
#   1. Wait for token to expire (bad UX)
#   2. Store permissions in database and check (defeats "stateless")
#   3. Revoke token via blacklist (defeats "stateless")
```

**Problem**: Changes to user permissions take up to 15 minutes to take effect.
**Irony**: Stateless tokens are less responsive to change than stateful sessions.

#### 3. **Token Size**

**Session Token:**
```
Cookie: session_id=abc123def456
# 20 bytes
```

**JWT Token:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ...
# 500+ bytes
```

**Problem**: Every request sends more data over network.
**Impact**: Matters for millions of requests per second.

#### 4. **Token Revocation**

**Scenario**: User's account is compromised. Attacker has their token. Can we revoke it?

**With Sessions:**
```python
DELETE FROM sessions WHERE user_id = 123
# Immediate. User logged out, attacker locked out.
```

**With JWT:**
```python
# Token still valid for 15 minutes
# Options:
#   1. Wait for expiry (attacker has access for 15 min)
#   2. Blacklist token (need database lookup)
#   3. Blacklist all user's tokens (still need database)
```

**Problem**: Revocation is not instant.
**Impact**: Security incident response is delayed.

#### 5. **Debugging & Observability**

**Session Approach:**
```python
# Server logs show which user is doing what
SELECT * FROM sessions WHERE session_id = 'abc'
# User associated with this session: alice

# Can track user's behavior across requests
# Can see when user was last active
# Can revoke specific session
```

**JWT Approach:**
```python
# Token is just data, no server record
# Can't easily track which user logged in via which method
# Can't see when user was last active
# Can't revoke single token (must blacklist all or wait for expiry)
```

**Problem**: Lost observability and debugging information.

#### 6. **Vulnerability to XSS**

**Token Storage:**
```
Option 1: localStorage
  Vulnerable to XSS (JavaScript can read it)
  Attacked could steal token

Option 2: HttpOnly cookie
  Protected from XSS (JavaScript can't read)
  But then you have CSRF vulnerabilities
  Back to using server state to verify cookies

Option 3: Memory
  Lost on refresh (poor UX)
```

**Problem**: JWT storage is hard to get right.

### The Verdict

**JWTs are good for:**
- ✅ Microservices (different services, shared token)
- ✅ Mobile apps (no cookie support)
- ✅ APIs where you control both client & server
- ✅ Stateless architectures at internet scale

**Sessions are better for:**
- ✅ Traditional web apps
- ✅ Immediate permission changes
- ✅ Fine-grained security (revoke single session)
- ✅ Observability & debugging

**Hybrid is often best:**
- ✅ Short-lived JWT access token (15 min)
- ✅ Long-lived refresh token (7 days, revocable)
- ✅ Optional: Database lookup for critical operations

### Industry Evolution

**2015:** JWT is the future! Kill sessions!
**2017:** JWTs scale better
**2020:** Actually, stateful sessions still useful...
**2023:** Use both. Refresh token = session, access token = JWT.
**2024:** Passkeys are the future (no passwords or tokens)

### The Honest Answer

> **JWT vs Sessions is not a binary choice.**
> 
> Use JWTs for:
> - Access tokens (short-lived, carry info)
> - Distributed systems (any server can verify)
> 
> Use Sessions/Databases for:
> - Refresh tokens (long-lived, revocable)
> - Permission checks (immediate updates)
> - Logout (instant revocation)
> - Audit logs (track behavior)
> 
> The best systems use both.

### Further Reading

- ["Stop Using JWTs for Sessions" (Reddit)](https://www.reddit.com/r/golang/comments/mde0j1/session_management_in_golang/)
- ["JWTs vs Sessions: Let's Talk About It" (Auth0 Blog)](https://auth0.com/blog/jwt-faq/)
- ["Logout? This Time for Real" (Medium)](https://medium.com/@chrismendez/logout-with-json-web-tokens-jwt-what-the-heck-is-it-54b4b05d0d83)
- RFC 7519: JSON Web Token (JWT)

---

## Summary: Week 1 Review

You now understand:
1. **How JWTs work**: Signed tokens with claims and expiry
2. **How passwords work**: Hashed with bcrypt (one-way, salted, slow)
3. **How registration works**: Validate input, hash password, store
4. **How login works**: Verify hash, create JWT, return token
5. **How protected routes work**: Extract token, verify signature, return data
6. **What happens if intercepted**: Token is usable until expiry (need HTTPS)
7. **Edge cases**: Expired, tampered, wrong secret, missing claim, deleted user
8. **JWT tradeoffs**: Stateless but needs blacklist for logout

## Next Steps

Week 2:
- Refresh tokens (separate long-lived tokens)
- Logout implementation (token blacklist)
- Email verification (confirm email ownership)
- Password reset (forgotten password flow)

The foundation is solid. Keep building.
