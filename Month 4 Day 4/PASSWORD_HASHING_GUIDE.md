# Day 4: Password Hashing — Never Store Plain Passwords

## The Rule

**Never store plain passwords in a database.** This is not a suggestion — it's a foundational security principle that separates responsible applications from ones that leak user accounts.

## Install Passlib + Bcrypt

```bash
pip install passlib[bcrypt]
```

This gives you:
- `passlib.context.CryptContext` — hash and verify passwords
- `bcrypt` backend — slow by design, automatically salted

## Core Concepts

### CryptContext: Hash & Verify

```python
from passlib.context import CryptContext

# Setup (once, at module level)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Cost: ~100ms per hash on modern hardware
)

# Hash a password (at signup)
hashed = pwd_context.hash("alice123")
# Result: $2b$12$abcdefghijklmnop...xyz (60 chars, always different)

# Verify a password (at login)
is_correct = pwd_context.verify("alice123", hashed)  # → True
is_correct = pwd_context.verify("wrong", hashed)      # → False
```

### Why Bcrypt (or Argon2)?

| Feature | Plain Hash (SHA256) | Bcrypt |
|---------|-----|---------|
| Speed | microseconds | 100-500ms ✓ |
| Salted | No | Yes, automatic ✓ |
| Reversible | No | No ✓ |
| Brute force | 1 billion guesses/sec | 1 guess/sec ✓ |
| Scales with hardware | No | Yes, via cost parameter ✓ |
| Standard | Yes | Yes ✓ |

**Speed is a feature.** Bcrypt's slowness makes it secure:
- User login takes 100ms (imperceptible)
- Attacker's brute force takes 1sec per guess
- 1 million passwords = 278 years to crack one

### The Hash Format

```
$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW
 ↑  ↑  ↑                ↑
 |  |  |                └─ salt (22 chars) + hash (31 chars)
 |  |  └─ cost parameter (2^12 = 4096 rounds)
 |  └─ bcrypt version ($2b = latest safe version)
 └─ algorithm identifier
```

Each hash is unique because the salt is random.

## Database Schema

### Before (VULNERABLE)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    password VARCHAR(255),  -- ✗ PLAIN TEXT - DANGER!
    email VARCHAR(255)
);

-- Database rows
alice  | alice123          | alice@example.com
bob    | qwerty99          | bob@example.com
eve    | password1         | eve@example.com
```

If leaked:
- Attacker has all passwords instantly
- Can log in as anyone
- Can try these passwords on other sites

### After (SECURE)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    hashed_password VARCHAR(60),  -- ✓ BCRYPT HASH (always 60 chars)
    email VARCHAR(255)
);

-- Database rows
alice  | $2b$12$R9h/cIPz0gi.URNNX3kh2O...  | alice@example.com
bob    | $2b$12$E8dg/cIPz0gi.URNNX3kh2O...  | bob@example.com
eve    | $2b$12$L3k/cIPz0gi.URNNX3kh2O...   | eve@example.com
```

If leaked:
- Attacker has one-way hashes
- Cannot reverse to get password
- Brute force is slow (1 guess/sec)
- Even with 1 year of guessing, maybe cracks 1 password

## FastAPI Implementation

### 1. Setup

```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)
```

### 2. At Signup (Hash & Store)

```python
@app.post("/auth/signup")
async def signup(username: str, password: str, email: str):
    # 1. Hash the password
    hashed_password = pwd_context.hash(password)  # ✓ Takes ~100ms
    
    # 2. Store HASH in database (not plain password)
    db.users.insert({
        "username": username,
        "hashed_password": hashed_password,  # ✓ Store this
        "email": email
    })
    
    # 3. Return success (never return password or hash)
    return {"message": "Signup successful"}
```

### 3. At Login (Verify)

```python
def authenticate_user(username: str, password: str):
    # 1. Get user from database
    user = db.users.find_one({"username": username})
    if not user:
        return None  # User doesn't exist
    
    # 2. Verify password against stored hash
    # ✓ This is constant-time, resists timing attacks
    if not pwd_context.verify(password, user["hashed_password"]):
        return None  # Wrong password
    
    # 3. Password is correct
    return user

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Bad credentials")
    
    # Issue JWT (same as Day 3)
    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}
```

## Migration: Plain Text → Hashed (for existing databases)

**Problem:** Your database has plain text passwords. You need to hash them without locking out users.

### Migration Strategy

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def migrate_passwords():
    """
    One-time script to hash all existing plain text passwords.
    Run once, then delete this script.
    """
    users = db.users.find()  # Get all users
    
    for user in users:
        # Check if already hashed (hashes start with $2b$)
        if user["password"].startswith("$2b$"):
            print(f"✓ {user['username']} already hashed")
            continue
        
        # Hash the plain text password
        hashed = pwd_context.hash(user["password"])
        
        # Update database with hash
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"hashed_password": hashed}}
        )
        
        # Delete plain text field (optional, but recommended)
        db.users.update_one(
            {"_id": user["_id"]},
            {"$unset": {"password": ""}}
        )
        
        print(f"✓ {user['username']} migrated")

# Run once at startup (or as one-time script)
if __name__ == "__main__":
    migrate_passwords()
    print("✓ Migration complete")
```

### During Migration (Minimize Downtime)

```python
# During transition, support both fields
def authenticate_user_transitional(username: str, password: str):
    user = db.users.find_one({"username": username})
    if not user:
        return None
    
    # Try hashed first (new users)
    if "hashed_password" in user:
        if pwd_context.verify(password, user["hashed_password"]):
            return user
    
    # Fall back to plain text (old users, during migration)
    if "password" in user and user["password"] == password:
        # Hash it now for next login
        hashed = pwd_context.hash(password)
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"hashed_password": hashed}}
        )
        return user
    
    return None
```

## Common Mistakes

### ❌ Storing plain passwords
```python
# WRONG
db.users.insert({
    "username": username,
    "password": password  # ✗ NEVER do this
})
```

### ❌ Using `==` to compare passwords
```python
# WRONG
if user["password"] == entered_password:  # ✗ Timing attack risk
    # login
```

### ❌ Trying to reverse a hash
```python
# WRONG
original_password = reverse_hash(stored_hash)  # ✗ Impossible & wrong design
```

### ❌ Returning hashed password in API
```python
# WRONG
@app.get("/api/me")
async def get_user(user = Depends(get_current_user)):
    return {
        "username": user.username,
        "hashed_password": user.hashed_password  # ✗ Never expose
    }

# RIGHT
@app.get("/api/me")
async def get_user(user = Depends(get_current_user)):
    return {
        "username": user.username,
        # Don't include hashed_password
    }
```

## Testing

```python
import pytest
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_password_hashing():
    password = "test123"
    
    # Test hashing
    hashed = pwd_context.hash(password)
    assert len(hashed) == 60  # Bcrypt always produces 60-char hash
    assert hashed.startswith("$2b$")  # Bcrypt identifier
    assert hashed != password  # Not the same as plain text
    
    # Test verification
    assert pwd_context.verify(password, hashed)  # Correct password
    assert not pwd_context.verify("wrong", hashed)  # Wrong password
    
    # Test uniqueness (same password = different hash)
    hashed2 = pwd_context.hash(password)
    assert hashed != hashed2  # Different hashes
    assert pwd_context.verify(password, hashed2)  # But both verify

def test_timing_attack_resistance():
    """
    pwd_context.verify() is constant-time.
    Doesn't leak information about where password differs.
    """
    password = "correct"
    hashed = pwd_context.hash(password)
    
    # Should take same time regardless of where mismatch is
    pwd_context.verify("a", hashed)      # First char wrong
    pwd_context.verify("correc_", hashed)  # Last char wrong
    pwd_context.verify("x" * 100, hashed)  # Long wrong password
    # All take ~same time (hard to measure, but bcrypt does this)
```

## Compliance

Hashing passwords is required by:
- **GDPR** (Europe) — secure processing of personal data
- **CCPA** (California) — reasonable security practices
- **PCI-DSS** (Payment Card Industry) — if you store credit cards
- **SOC 2** — if you handle sensitive data
- **HIPAA** (US Healthcare) — protected health info
- **Industry standard** (OWASP, NIST)

Failing to hash passwords can result in:
- Lawsuits
- Regulatory fines (up to millions)
- Loss of trust
- Requirement to notify users of breach
- Criminal liability (in some jurisdictions)

## Next Steps (Day 5)

- Refresh tokens (long-lived, secure token rotation)
- Token blacklist/revocation (logout before expiry)
- Password reset (secure token-based reset link)
- Rate limiting (prevent brute force on login)
- Multi-factor authentication (2FA)
