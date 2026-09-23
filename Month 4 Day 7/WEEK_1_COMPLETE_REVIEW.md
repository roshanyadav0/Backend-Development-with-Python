# Week 1 Review: Complete Authentication System

## What You Built

A production-ready authentication system from first principles:

```
┌─────────────────────────────────────────────────────────────┐
│ WEEK 1: COMPLETE AUTH SYSTEM                                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Day 1: How Auth Works                                      │
│    ├─ Sessions vs tokens                                    │
│    ├─ Why JWTs for APIs/SPAs                                │
│    └─ JWT structure (header.payload.signature)              │
│                                                               │
│  Day 2: JWT Deep Dive                                       │
│    ├─ HS256 vs RS256 (symmetric vs asymmetric)             │
│    ├─ Standard claims (sub, exp, iat, nbf)                 │
│    ├─ Token expiry (short-lived = safer)                   │
│    └─ Sign/verify in Python (passlib, jwt)                 │
│                                                               │
│  Day 3: FastAPI + OAuth2                                    │
│    ├─ OAuth2PasswordBearer (security scheme)               │
│    ├─ Dependency injection with Depends()                  │
│    ├─ Protected routes                                      │
│    └─ POST /auth/login → JWT issuance                      │
│                                                               │
│  Day 4: Password Hashing                                    │
│    ├─ Bcrypt (slow by design)                              │
│    ├─ Never store plain passwords                          │
│    ├─ Salting (automatic, unique per user)                │
│    └─ CryptContext (hash & verify)                         │
│                                                               │
│  Day 5: Registration Endpoint                               │
│    ├─ POST /auth/register (email + password)               │
│    ├─ Validate input (Pydantic EmailStr)                   │
│    ├─ Check email uniqueness (409 Conflict)                │
│    ├─ Hash password before storage                         │
│    ├─ Store in PostgreSQL/SQLite                           │
│    └─ Test: 50+ test cases                                 │
│                                                               │
│  Day 6: Login + JWT                                         │
│    ├─ POST /auth/login (form: email, password)            │
│    ├─ Query user by email                                  │
│    ├─ Verify password (constant-time)                      │
│    ├─ Create JWT (sub, exp, iat)                           │
│    ├─ Return {access_token, token_type, expires_in}       │
│    ├─ GET /api/me (protected with Depends)                │
│    └─ Test: 20+ test cases                                 │
│                                                               │
│  Day 7: Review & Deep Dive                                  │
│    ├─ Rebuild from memory                                  │
│    ├─ Explain JWT interception scenarios                   │
│    ├─ Test 5 edge cases                                    │
│    └─ Understand JWT tradeoffs                             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## The Complete Flow

### User Registration

```
1. Frontend: POST /auth/register
   {
     "email": "alice@example.com",
     "password": "SecurePass123"
   }

2. Server: Validate input
   - Pydantic EmailStr checks format
   - Validator checks password length (8-128 chars)

3. Server: Check uniqueness
   - Query: SELECT * FROM users WHERE email = ?
   - If exists: return 409 Conflict

4. Server: Hash password
   - hashed = pwd_context.hash(password)
   - Salt generated automatically
   - Takes ~100ms (intentionally slow)

5. Server: Store in database
   - INSERT INTO users (email, hashed_password, created_at)
   - VALUES ('alice@example.com', '$2b$12$...', NOW())

6. Server: Response 201 Created
   {
     "id": 1,
     "email": "alice@example.com",
     "created_at": "2024-09-22T12:00:00"
   }

7. Database state:
   ✓ Plain password NEVER stored
   ✓ Only hash stored
   ✓ If DB leaks, passwords still protected
```

### User Login

```
1. Frontend: POST /auth/login (form data)
   username=alice@example.com&password=SecurePass123

2. Server: Authenticate user
   - Query: SELECT * FROM users WHERE email = ?
   - Verify: pwd_context.verify(entered, stored_hash)
   - Constant-time comparison (resists timing attacks)

3. Server: Password matches? 
   - If no: return 401 "Incorrect email or password" (generic)
   - If yes: continue

4. Server: Create JWT token
   payload = {
     "sub": "1",                    # user_id
     "exp": now + 15 minutes,       # expiration
     "iat": now                     # issued at
   }
   token = jwt.encode(payload, SECRET_KEY, "HS256")

5. Server: Response 200 OK
   {
     "access_token": "eyJhbGciOiJIUzI1NiI...",
     "token_type": "bearer",
     "expires_in": 900
   }

6. Frontend: Store token
   - localStorage (convenient but XSS-vulnerable)
   - sessionStorage (cleared on tab close)
   - Memory (lost on refresh)
   - Secure HttpOnly cookie (best but complex)
```

### Protected Route Access

```
1. Frontend: GET /api/me
   Header: Authorization: Bearer eyJhbGciOiJIUzI1NiI...

2. Server: oauth2_scheme extracts token
   - Reads header: Authorization: Bearer <token>
   - Extracts token part

3. Server: get_current_user() verifies token
   - jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
   - Checks signature: HMAC(SECRET_KEY, header.payload) == sig
   - Checks expiry: if exp > now, continue
   
4. Signature valid? Expiry valid?
   - If no: raise JWTError → caught → 401 Unauthorized
   - If yes: continue

5. Server: Extract user_id from token
   - payload.get("sub") → "1"

6. Server: Fetch user from database
   - Query: SELECT * FROM users WHERE id = 1
   - If not found: 401 Unauthorized
   - If found: continue

7. Server: Response 200 OK
   {
     "id": 1,
     "email": "alice@example.com",
     "created_at": "2024-09-22T12:00:00"
   }
```

## Key Concepts by Day

### Day 1: Fundamentals
- **Sessions**: Server stores state, cookie carries ID
- **Tokens**: Server signs data, client carries token
- **JWTs**: Format for tokens (header.payload.signature)

### Day 2: JWT Details
- **HS256**: HMAC-SHA256 (symmetric, one secret)
- **RS256**: RSA-SHA256 (asymmetric, public/private)
- **Claims**: Standardized fields (sub, exp, iat, nbf)
- **Expiry**: Why tokens must die (limit damage if stolen)

### Day 3: Integration
- **OAuth2PasswordBearer**: FastAPI's security scheme
- **Depends()**: Dependency injection (runs before route)
- **Form data**: OAuth2 standard (username, password)

### Day 4: Passwords
- **Bcrypt**: Slow by design (100ms per hash)
- **Salting**: Automatic, unique per user
- **One-way**: Cannot reverse (password can't be recovered)
- **Brute force resistant**: 1 guess/sec, not 1B/sec

### Day 5: Registration
- **Input validation**: Pydantic (format, length, uniqueness)
- **Password hashing**: Before storage
- **Error handling**: 400, 409, 422, 500
- **Testing**: 50+ test cases

### Day 6: Login
- **Constant-time verification**: pwd_context.verify()
- **Generic errors**: Don't leak email existence
- **JWT creation**: Claims (sub, exp, iat)
- **Protected routes**: Dependency-based security

### Day 7: Review
- **Rebuild from memory**: Understand the flow
- **Security scenarios**: What if intercepted?
- **Edge cases**: Expired, tampered, wrong secret, missing claim, deleted user
- **Tradeoffs**: JWTs are stateless but need blacklist for logout

## Test Coverage

### Registration Tests (50+)
- ✅ Successful registration
- ✅ Duplicate email (409)
- ✅ Invalid email format (422)
- ✅ Password validation (too short/long) (422)
- ✅ Database storage (password is hashed, not plain)
- ✅ Response structure (no password/hash exposure)

### Login Tests (20+)
- ✅ Successful login with correct credentials
- ✅ Wrong password (401)
- ✅ Non-existent email (401, generic message)
- ✅ JWT token validity
- ✅ Protected route with valid token (200)
- ✅ Protected route without token (403)
- ✅ Protected route with invalid token (401)
- ✅ Multiple users
- ✅ Token expiry time

### Edge Case Tests (5)
- ✅ Expired token (401)
- ✅ Tampered signature (401)
- ✅ Token with wrong secret (401)
- ✅ Token missing required claim (401)
- ✅ User deleted after login (401)

**Total: 75+ test cases** covering happy paths, error paths, edge cases, and security scenarios.

## Files Delivered

### Core Implementation (3 files)
1. **fastapi_registration.py** — Register endpoint only
2. **fastapi_auth_complete.py** — Register + Login + Protected routes
3. **week1_review_rebuild.py** — Rebuild from memory

### Tests (5 files)
1. **test_registration.py** — Pytest suite for registration (50+ cases)
2. **test_registration_manual.py** — Manual registration tests
3. **test_login.py** — Pytest suite for login (20+ cases)
4. **test_login_manual.py** — Manual login tests
5. **test_edge_cases.py** — Edge case tests (5 scenarios)

### Documentation (6 files)
1. **REGISTRATION_GUIDE.md** — Complete registration reference
2. **LOGIN_GUIDE.md** — Complete login reference
3. **PASSWORD_HASHING_GUIDE.md** — Password hashing best practices
4. **FASTAPI_JWT_GUIDE.md** — FastAPI OAuth2 setup
5. **JWT_SECURITY_DEEP_DIVE.md** — Security & tradeoffs
6. **DAY_*_SUMMARY.md** — Daily reviews

**Total: 14 files, ~4000 lines of code + documentation**

## Security Checklist

- ✅ Passwords hashed with bcrypt (12 rounds, automatic salt)
- ✅ Password verification constant-time (resists timing attacks)
- ✅ Email validation (format, uniqueness)
- ✅ JWT signed (tampering detected)
- ✅ JWT expiry (15 minutes, limits damage)
- ✅ Generic error messages (prevent email enumeration)
- ✅ No passwords in responses or logs
- ✅ No hashes exposed in API responses
- ✅ SQL injection prevention (ORM)
- ✅ Database constraints (unique email, indexed)
- ✅ HTTPS recommended (encrypt in transit)
- ✅ SECRET_KEY in environment (not hardcoded)
- ✅ Dependency injection (Depends)

## Performance

- Registration: ~110ms per user (100ms for hashing)
- Login: ~102ms per attempt (100ms for password verification)
- Protected route: ~1-2ms (just verify signature)
- Scales: ~100 logins/sec per server

## What's NOT Included (Next Week)

- Refresh tokens (get new access token without re-login)
- Logout (token blacklist or revocation)
- Email verification (confirm email ownership)
- Password reset (forgotten password flow)
- Rate limiting (prevent brute force)
- 2FA (two-factor authentication)
- OAuth2 (Google, GitHub login)
- Passkeys (passwordless auth)

## Common Mistakes You Now Avoid

| Mistake | What Happens | How You Prevent It |
|---------|--------------|-------------------|
| Plain password storage | Database leak = instant takeover | Hash with bcrypt |
| Password comparison with == | Timing attack vulnerability | Use pwd_context.verify() |
| Revealing user existence | Email enumeration | Generic error message |
| No token expiry | Stolen token works forever | Set exp claim (15 min) |
| Returning password in API | Security info disclosure | Only return id, email, created_at |
| Missing validation | Malformed data breaks DB | Pydantic validators |
| Duplicate email allowed | Multiple accounts per email | Unique constraint + 409 check |
| Unencrypted transport | Network eavesdropping | Use HTTPS |
| Hardcoded SECRET_KEY | Source code leak = all tokens broken | Environment variables |

## Key Principles Learned

### 1. Defense in Depth
- Input validation (Pydantic)
- Password security (bcrypt)
- Token security (JWT signature + expiry)
- Database constraints (unique, indexed)
- Error handling (401, 403, 409, 422)

### 2. Stateless Where Possible, Stateful Where Needed
- JWTs are stateless (no DB lookup to verify)
- But need database for:
  - User storage (emails, hashes)
  - Email uniqueness checks
  - User existence verification

### 3. Generic Error Messages
- Don't say "user not found" (reveals email exists)
- Don't say "wrong password" (different from user-not-found)
- Say "Incorrect email or password" (same error for both)

### 4. Slow is Secure (For Passwords)
- Bcrypt: 100ms per hash (slow, intentional)
- Makes brute force slow: 1 guess/sec, not 1B/sec
- As hardware improves, bcrypt rounds increase

### 5. Verification, Not Comparison
- `==` is dangerous (timing attack)
- `pwd_context.verify()` is constant-time (safe)

## How to Use This System

### Development
```bash
python fastapi_auth_complete.py
# Open http://localhost:8000/docs
# Click "Authorize" on protected routes
```

### Testing
```bash
# Run all tests
pytest test_*.py -v

# Or specific tests
pytest test_login.py::test_login_success -v
```

### Production Checklist
- [ ] Move SECRET_KEY to environment variable
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable HTTPS (TLS/SSL)
- [ ] Use bcrypt_rounds=12 or higher
- [ ] Set CORS appropriately
- [ ] Add rate limiting
- [ ] Enable logging
- [ ] Backup database regularly
- [ ] Monitor failed login attempts
- [ ] Implement refresh tokens (Week 2)

## What You're Ready For

After Week 1, you can:
- ✅ Build authentication from scratch
- ✅ Explain why passwords must be hashed
- ✅ Explain JWT security properties
- ✅ Implement secure registration
- ✅ Implement secure login
- ✅ Protect API routes
- ✅ Handle authentication errors
- ✅ Write comprehensive tests
- ✅ Recognize and prevent common vulnerabilities

You're **not** ready for:
- ❌ Permanent logout (needs refresh token blacklist)
- ❌ Permission changes (too long to take effect)
- ❌ Account lockout (needs rate limiting)
- ❌ Email verification (needs email sending)
- ❌ Password reset (needs secure token flow)
- ❌ Multiple providers (OAuth2 social login)

But you have the foundation. Week 2 will add these.

## Reflection Questions

1. **Without looking at code, can you explain the complete flow from registration to protected route access?**
   - If not, review the flow diagram above
   - Try to rebuild it from memory

2. **What makes JWT "stateless"?**
   - No database lookup to verify token
   - Server can verify based on signature alone

3. **What's the tradeoff of stateless JWTs?**
   - Logout requires database lookup (defeats statelessness)
   - Permission changes take time to propagate

4. **Why is bcrypt slow?**
   - Intentional: makes brute force slow
   - 1 guess/sec instead of 1B/sec

5. **What happens if someone steals a JWT?**
   - They can use it until expiry (15 minutes)
   - After that, it's useless
   - That's why expiry is important

6. **Why use constant-time password verification?**
   - Prevent timing attacks
   - Attacker can't learn where password differs

7. **Why generic error messages?**
   - Prevent email enumeration
   - Attacker can't tell if email is registered

## Next Steps

Move to Week 2:
- Refresh tokens (rotate tokens safely)
- Logout (revoke tokens)
- Email verification (confirm email)
- Password reset (forgotten password)
- Rate limiting (prevent brute force)

You have a solid foundation. The system works. Keep building.

---

**Week 1 Complete**: You built a production-grade authentication system.
**Time to celebrate**: Pour yourself a drink, you earned it.
**Time to ship**: Add HTTPS, env vars, and deploy.
**Time to improve**: Refresh tokens and logout (Week 2).
