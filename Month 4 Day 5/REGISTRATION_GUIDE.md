# Day 5: Registration Endpoint

## Complete User Registration Flow

Register new users with email + password:
1. **Validate input** — Email format, password strength
2. **Check uniqueness** — Email not already registered
3. **Hash password** — Never store plain text
4. **Store in database** — Save email + hashed password
5. **Return success** — 201 Created with user info (no password)

## Install Dependencies

```bash
pip install fastapi sqlalchemy psycopg2-binary passlib[bcrypt] pydantic[email] pytest httpx
```

Components:
- `fastapi` — API framework
- `sqlalchemy` — ORM for database
- `psycopg2-binary` — PostgreSQL driver
- `passlib[bcrypt]` — Password hashing
- `pydantic[email]` — Email validation (EmailStr)
- `pytest` — Testing framework
- `httpx` — HTTP client for tests

## Database Setup

### SQLite (Local Testing)

No setup needed. SQLite is built-in:

```python
DATABASE_URL = "sqlite:///./auth.db"
```

Starts working immediately.

### PostgreSQL (Production)

```bash
# 1. Install PostgreSQL
# macOS: brew install postgresql
# Ubuntu: sudo apt install postgresql
# Windows: Download from postgresql.org

# 2. Start PostgreSQL service
# macOS: brew services start postgresql
# Ubuntu: sudo systemctl start postgresql
# Windows: Start PostgreSQL service

# 3. Create database and user
psql -U postgres
```

Then in `psql`:

```sql
CREATE USER authuser WITH PASSWORD 'securepassword';
CREATE DATABASE authdb OWNER authuser;
GRANT ALL PRIVILEGES ON DATABASE authdb TO authuser;
\q
```

Update connection string:

```python
DATABASE_URL = "postgresql://authuser:securepassword@localhost/authdb"
```

## API Usage

### Register a User

**Request:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "SecurePass123"
  }'
```

**Successful Response (201):**
```json
{
  "id": 1,
  "email": "alice@example.com",
  "created_at": "2024-09-17T12:34:56",
  "message": "User registered successfully"
}
```

**Duplicate Email (409):**
```json
{
  "detail": "Email already registered"
}
```

**Invalid Email (422):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "invalid email address"
    }
  ]
}
```

**Password Too Short (422):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "password"],
      "msg": "Password must be at least 8 characters"
    }
  ]
}
```

### List Users (Debug Only)

```bash
curl http://localhost:8000/auth/users
```

**Response:**
```json
[
  {
    "id": 1,
    "email": "alice@example.com",
    "created_at": "2024-09-17T12:34:56"
  },
  {
    "id": 2,
    "email": "bob@example.com",
    "created_at": "2024-09-17T12:35:00"
  }
]
```

## Running the Server

```bash
# Terminal 1: Start server
python fastapi_registration.py

# Output:
# ============================================================
# FastAPI Registration API
# ============================================================
#
# Database: sqlite:///./auth.db
#
# Endpoints:
#   POST   /auth/register    — Register a new user
#   GET    /auth/users       — List all users (debug only)
#   GET    /health           — Health check
#
# 📚 API Docs: http://localhost:8000/docs
```

Open http://localhost:8000/docs for interactive Swagger UI.

## Running Tests

```bash
# Terminal 2: Run all tests
pytest test_registration.py -v

# Output:
# test_register_user_success PASSED
# test_register_user_in_database PASSED
# test_register_duplicate_email_conflict PASSED
# test_register_invalid_email_format PASSED
# test_register_password_too_short PASSED
# ... etc
```

### Running Specific Tests

```bash
# Run one test
pytest test_registration.py::test_register_user_success -v

# Run tests matching a pattern
pytest test_registration.py -k "duplicate" -v

# Verbose output with print statements
pytest test_registration.py -v -s
```

## Code Walkthrough

### 1. User Model (SQLAlchemy)

```python
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)  # ✓ Unique constraint
    hashed_password = Column(String)  # ✓ Store hash, not plain
    created_at = Column(DateTime, server_default=func.now())
```

### 2. Input Validation (Pydantic)

```python
class UserRegisterRequest(BaseModel):
    email: EmailStr  # ✓ Validates email format
    password: str
    
    @validator('password')
    def password_valid(cls, v):
        if len(v) < 8:  # ✓ Min length
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:  # ✓ Max length
            raise ValueError('Password must be at most 128 characters')
        return v
```

### 3. Registration Logic

```python
@app.post("/auth/register", status_code=201)
async def register(user_data: UserRegisterRequest, db: Session):
    # Step 1: Validate (automatic via Pydantic)
    # Step 2: Check uniqueness
    existing = db.query(UserDB).filter(
        UserDB.email == user_data.email
    ).first()
    if existing:
        raise HTTPException(409, "Email already registered")
    
    # Step 3: Hash password
    hashed = pwd_context.hash(user_data.password)
    
    # Step 4: Store in DB
    db_user = UserDB(email=user_data.email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Step 5: Return user (no password/hash)
    return UserResponse(id=db_user.id, email=db_user.email, ...)
```

## Security Checklist

- ✅ **Password hashing**: bcrypt, 12 rounds, automatic salt
- ✅ **Email validation**: Pydantic EmailStr validates format
- ✅ **Duplicate prevention**: DB unique constraint + app logic
- ✅ **No password in response**: Only return id, email, created_at
- ✅ **No hash in response**: Never expose hashed_password
- ✅ **Password strength**: Min 8, max 128 chars
- ✅ **Error messages**: Generic messages don't leak info
- ✅ **SQL injection prevention**: SQLAlchemy ORM escapes automatically
- ✅ **Database errors**: Caught and logged, generic response

## Common Errors & Fixes

### Error: `ModuleNotFoundError: No module named 'sqlalchemy'`
```bash
pip install sqlalchemy
```

### Error: `No password supplied` (PostgreSQL)
```bash
# Make sure PostgreSQL is running
# macOS: brew services start postgresql
# Ubuntu: sudo systemctl start postgresql
```

### Error: `database is locked` (SQLite)
Delete `auth.db` and restart:
```bash
rm auth.db
python fastapi_registration.py
```

### Error: `email field is required`
Pydantic validation failed. Check email format:
```json
{"email": "user@example.com"}  // ✓ Valid
{"email": "user.example.com"}  // ✗ No @
```

### Error: `Email already registered` on first register
Database has old data. Delete DB and retry:
```bash
rm auth.db
```

## Next: Next Steps (Day 6+)

- Login endpoint with JWT (Days 3-4 + this registration)
- Email verification (send confirmation link)
- Password reset (forgot password flow)
- Rate limiting (prevent brute force on registration)
- CAPTCHA (prevent bot registrations)

## Files

- **fastapi_registration.py** — Main app with registration endpoint
- **test_registration.py** — Pytest tests (50+ test cases)
- **PASSWORD_HASHING_GUIDE.md** — Day 4 reference (from earlier)

## Example: Full Integration

Combine Days 1-5:

```python
# Day 3: OAuth2PasswordBearer setup
# Day 4: Password hashing with bcrypt
# Day 5: Registration endpoint

# Flow:
# 1. User POST /auth/register → creates account
# 2. User POST /auth/login → gets JWT token
# 3. User GET /api/me → protected with token
```

## Database Schema (PostgreSQL)

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(60) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

## Load Testing

Test with many registrations:

```python
import requests
import concurrent.futures
import time

BASE = "http://localhost:8000"

def register_user(i):
    response = requests.post(
        f"{BASE}/auth/register",
        json={
            "email": f"user{i}@test.com",
            "password": "SecurePass123"
        }
    )
    return response.status_code

# Register 100 users in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    start = time.time()
    results = list(executor.map(register_user, range(100)))
    elapsed = time.time() - start

print(f"Registered 100 users in {elapsed:.2f}s")
print(f"Success rate: {sum(1 for r in results if r == 201)} / 100")
```

## Monitoring

Add logging to track registrations:

```python
import logging

logger = logging.getLogger(__name__)

@app.post("/auth/register")
async def register(...):
    logger.info(f"Registration attempt: {user_data.email}")
    try:
        # ... registration logic
        logger.info(f"Registration successful: {db_user.id}")
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise
```

## Database Migrations (Future)

For production, use Alembic:

```bash
pip install alembic

alembic init migrations
alembic revision --autogenerate -m "Create users table"
alembic upgrade head
```

This lets you version-control schema changes.
