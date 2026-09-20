# Day 4: Password Hashing — Never Store Plain Passwords

## The Core Principle

**Never store plain text passwords.** This is absolute. No exceptions. If your database is leaked, hashed passwords give users a fighting chance. Plain passwords = instant account takeover for everyone.

## What You Learned

### 1. Why Hashing Matters

**Plain text passwords (DANGEROUS):**
```
Database leaked:
  → Attacker has all passwords
  → Instant access to all accounts
  → Passwords reused on other sites
  → No recovery
  → Lawsuits, fines, prison (depending on jurisdiction)
```

**Hashed passwords (SAFE):**
```
Database leaked:
  → Attacker has one-way hashes
  → Cannot reverse back to passwords
  → Brute force takes months/years per password
  → Users get notified, can change password
  → Minimal damage
```

### 2. Bcrypt (or Argon2)

Bcrypt is **intentionally slow** — this is a feature:
- **One-way:** Cannot reverse a hash
- **Salted:** Automatic, unique per user, embedded in hash
- **Slow:** 100-500ms per hash (brute force is 1 guess/sec)
- **Cost scalable:** As hardware improves, increase rounds
- **Proven:** Industry standard for 20+ years

Comparison:

| Property | MD5/SHA256 | Bcrypt |
|----------|----------|---------|
| Time per hash | 1 microsecond | 100ms |
| Reversible | No | No |
| Salted | No | Yes (auto) |
| Brute force speed | 1B guesses/sec | 1 guess/sec |
| Cost parameter | N/A | 2^12...14 |

### 3. CryptContext: The Tool

```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # ~100ms per hash
)

# Hash (at signup)
hashed = pwd_context.hash("alice123")
# → $2b$12$R9h/cIPz0gi.URNNX3kh2O... (60 chars)

# Verify (at login)
is_correct = pwd_context.verify("alice123", hashed)  # → True
is_correct = pwd_context.verify("wrong", hashed)      # → False
```

### 4. Integration with FastAPI

**At Signup (hash & store):**
```python
@app.post("/auth/signup")
async def signup(username: str, password: str):
    hashed = pwd_context.hash(password)  # ✓ Hash
    db.users.insert({
        "username": username,
        "hashed_password": hashed  # ✓ Store hash (not plain)
    })
    return {"message": "Signup successful"}
```

**At Login (verify):**
```python
def authenticate_user(username: str, password: str):
    user = db.users.find_one({"username": username})
    # ✓ Use verify() — constant-time, resists timing attacks
    if not pwd_context.verify(password, user["hashed_password"]):
        return None
    return user

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Bad credentials")
    
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
```

**In API responses (never expose hash):**
```python
# ✗ WRONG
return {"username": user.username, "hashed_password": user.hashed_password}

# ✓ RIGHT
return {"username": user.username}  # Only safe fields
```

### 5. Database Schema

**Old (vulnerable):**
```sql
CREATE TABLE users (
    username VARCHAR(255),
    password VARCHAR(255)  -- ✗ Plain text
);
```

**New (secure):**
```sql
CREATE TABLE users (
    username VARCHAR(255),
    hashed_password VARCHAR(60)  -- ✓ Bcrypt hashes (always 60 chars)
);
```

## Why Each Piece Matters

### Hash Length (60 characters)
Bcrypt always produces exactly 60 characters. This includes:
- Algorithm version (3 chars): `$2b$`
- Cost parameter (3 chars): `$12$`
- Salt (22 chars): random, unique per user
- Hash (31 chars): the actual encryption

If someone gives you a hash that's not 60 chars, it's not bcrypt.

### Cost Parameter (rounds=12)
`$2b$12$...` means 2^12 = 4096 rounds of hashing. This is the "slow" part:
- 2010: `rounds=10` ≈ 100ms (state of the art)
- 2024: `rounds=12` ≈ 100ms (modern hardware)
- 2040: `rounds=14` will ≈ 100ms (future-proofing)

As hardware gets faster, increase the parameter. Existing hashes still verify fine.

### Salt (Automatic & Unique)
Bcrypt embeds the salt in the hash:
- Same password → different hash for Alice vs Bob
- Each signup gets a new random salt
- Attacker can't use rainbow tables (pre-computed hashes)
- verify() knows to extract and use the salt automatically

### Timing Attack Resistance
`pwd_context.verify()` runs in constant time:
- Doesn't leak how many characters matched
- Doesn't leak which character failed first
- Never use `==` to compare passwords manually

## Common Mistakes to Avoid

### ❌ Comparing with `==`
```python
if user["password"] == entered_password:  # ✗ Vulnerable to timing attacks
    login()
```

### ❌ Trying to reverse a hash
```python
password = reverse_hash(stored_hash)  # ✗ Impossible, wrong design
```

### ❌ Hashing twice
```python
hashed = hash(hash(password))  # ✗ Doesn't add security, just slow
```

### ❌ Using password as salt
```python
hashed = sha256(password + password)  # ✗ Not secure, use bcrypt's auto-salt
```

### ❌ Returning hashed password in API
```python
return User(username=user.username, hashed_password=user.hashed_password)
# ✗ Exposes internal detail, even though it's hashed
```

## Installation

```bash
pip install passlib[bcrypt]
```

This installs:
- `passlib` — password hashing library
- `bcrypt` — the bcrypt algorithm

## Testing

```python
def test_password_security():
    hashed = pwd_context.hash("test123")
    
    # Verify correct password
    assert pwd_context.verify("test123", hashed)
    
    # Reject wrong password
    assert not pwd_context.verify("wrong", hashed)
    
    # Same password, different hash (due to salt)
    hashed2 = pwd_context.hash("test123")
    assert hashed != hashed2
    assert pwd_context.verify("test123", hashed2)
```

## What Changed from Day 3

| Day 3 | Day 4 |
|-------|-------|
| Fake user DB with plain passwords | Real hashed passwords |
| `verify_password()` compared plain text | `pwd_context.verify()` compares hashes |
| Demo only (not production-ready) | Production-ready pattern |
| No password hashing | Bcrypt hashing required |

## Files

- **fastapi_secure_auth.py** — Updated Day 3 app with real password hashing
- **PASSWORD_HASHING_GUIDE.md** — Comprehensive reference
- **password_hashing_demo.py** — Detailed examples (requires passlib install)

## Next Steps (Day 5+)

- Refresh tokens (rotate tokens safely)
- Logout / token blacklist (revoke tokens)
- Password reset (secure reset flows)
- Rate limiting (prevent brute force)
- Multi-factor authentication (2FA)

## Key Takeaway

Hashing passwords is not optional. It's a foundational security practice that every web application must implement. Use bcrypt (or Argon2), hash at signup, verify at login, never expose hashes. This single practice protects millions of users.

If you're building something that matters, do password hashing right.
