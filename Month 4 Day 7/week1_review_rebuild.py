#!/usr/bin/env python3
"""
Week 1 Review: Rebuild the complete auth flow from memory.

This is NOT a reference implementation. It's what you should be able to build
from scratch after Week 1, without looking at previous code.

Challenge: 
  - Register a user (email + password)
  - Hash password (bcrypt)
  - Login (verify hash, get JWT)
  - Access protected route (verify JWT)

Try building this without looking at fastapi_auth_complete.py!
"""

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, String, DateTime, Integer, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional

print("\n" + "="*70)
print("WEEK 1 REVIEW: REBUILD AUTH FROM MEMORY")
print("="*70)
print("""
This exercise asks you to rebuild the authentication system from scratch,
from memory, without looking at the full solutions.

Challenge tasks:
  1. Create database model for users
  2. Setup password hashing with bcrypt
  3. Create registration endpoint (email + password)
  4. Create login endpoint (verify hash, issue JWT)
  5. Create protected route (verify JWT)
  6. Handle errors (401, 409, 422)

Time limit: 30 minutes for each section
Ask: Can I explain what happens without looking at code?
""")

# ============================================================
# SECTION 1: DATABASE & HASHING SETUP
# ============================================================

print("\n" + "-"*70)
print("SECTION 1: DATABASE & HASHING SETUP")
print("-"*70)
print("""
Questions:
  1. What database model do we need for users?
     - What fields? (email, password, id, created_at)
     - What constraints? (email unique, id primary key)
  
  2. Why bcrypt?
     - One-way (can't reverse)
     - Salted (same password = different hash)
     - Slow (100ms, brute force resistant)
  
  3. How do we hash and verify?
     - Hash at signup: pwd_context.hash(password)
     - Verify at login: pwd_context.verify(entered, stored_hash)
""")

# Try to remember: set up CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# Try to remember: database setup
DATABASE_URL = "sqlite:///./week1_review.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Try to remember: User model
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, server_default=func.now())

Base.metadata.create_all(bind=engine)

print("✓ Database model created")
print("✓ Password hashing configured")

# ============================================================
# SECTION 2: PYDANTIC SCHEMAS
# ============================================================

print("\n" + "-"*70)
print("SECTION 2: PYDANTIC SCHEMAS")
print("-"*70)
print("""
Questions:
  1. What should registration request look like?
     - email (EmailStr validates format)
     - password (string, validate length)
  
  2. What should login response look like?
     - access_token (the JWT)
     - token_type (always "bearer")
     - expires_in (seconds until expiry)
  
  3. What should user response look like?
     - id, email, created_at (never password or hash!)
""")

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Min 8 chars')
        return v

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

print("✓ Request/response schemas defined")

# ============================================================
# SECTION 3: REGISTRATION LOGIC
# ============================================================

print("\n" + "-"*70)
print("SECTION 3: REGISTRATION LOGIC")
print("-"*70)
print("""
Questions:
  1. What steps does registration need?
     - Validate input (Pydantic does this automatically)
     - Check if email already exists (409 Conflict)
     - Hash password (pwd_context.hash)
     - Store in database
     - Return user (no password or hash!)
  
  2. Why hash before storing?
     - Never store plain passwords
     - If database leaks, passwords are still protected
     - Bcrypt makes brute force slow (1 guess/sec, not 1B/sec)
  
  3. Why check for duplicate email?
     - Each email should be unique
     - Each user should have one account
""")

SECRET_KEY = "your-secret-key-keep-safe-32-chars-minimum"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/auth/register", response_model=UserResponse, status_code=201)
async def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registration endpoint.
    
    Flow:
      1. Pydantic validates input (email format, password length)
      2. Check if email exists
      3. Hash password
      4. Store in database
      5. Return user (excluding password/hash)
    """
    # Step 1: Check if email already exists
    existing = db.query(UserDB).filter(UserDB.email == user_data.email).first()
    if existing:
        raise HTTPException(409, "Email already registered")
    
    # Step 2: Hash password
    hashed = pwd_context.hash(user_data.password)
    
    # Step 3: Store in database
    db_user = UserDB(email=user_data.email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Step 4: Return user (never expose hash)
    return db_user

print("✓ Registration endpoint implemented")

# ============================================================
# SECTION 4: LOGIN LOGIC
# ============================================================

print("\n" + "-"*70)
print("SECTION 4: LOGIN LOGIC")
print("-"*70)
print("""
Questions:
  1. What does login need to do?
     - Accept form data (email, password)
     - Query database for user
     - Verify password (pwd_context.verify, not ==)
     - Create JWT token
     - Return token (not password or user)
  
  2. Why verify, not compare?
     - pwd_context.verify() is constant-time
     - Doesn't leak info about where password differs
     - Resists timing attacks
  
  3. What claims should JWT have?
     - sub (subject = user ID)
     - exp (expiration = now + 15 min)
     - iat (issued at = now)
  
  4. Why generic error message?
     - "Incorrect email or password" for both user-not-found and wrong-password
     - Prevents attackers from enumerating valid emails
""")

def create_access_token(user_id: int) -> tuple[str, int]:
    """Create JWT token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    expires_in = int((expire - datetime.utcnow()).total_seconds())
    
    return token, expires_in

@app.post("/auth/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint.
    
    Flow:
      1. Query database for user
      2. Verify password (constant-time comparison)
      3. Create JWT
      4. Return token
    """
    # Step 1: Find user
    user = db.query(UserDB).filter(UserDB.email == form_data.username).first()
    
    # Step 2: Verify password
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        # Generic error message (don't reveal which part failed)
        raise HTTPException(401, "Incorrect email or password")
    
    # Step 3: Create JWT
    token, expires_in = create_access_token(user.id)
    
    # Step 4: Return token
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in
    }

print("✓ Login endpoint implemented")

# ============================================================
# SECTION 5: PROTECTED ROUTES
# ============================================================

print("\n" + "-"*70)
print("SECTION 5: PROTECTED ROUTES")
print("-"*70)
print("""
Questions:
  1. How do we protect a route with JWT?
     - Use Depends(oauth2_scheme) to extract token
     - Use Depends(get_current_user) to verify and get user
  
  2. What does jwt.decode() do?
     - Verifies signature (token wasn't tampered with)
     - Checks expiry (token isn't expired)
     - Returns payload
  
  3. What errors can occur?
     - Missing token: 403 (oauth2_scheme handles this)
     - Invalid signature: 401 (JWTError)
     - Expired token: 401 (ExpiredSignatureError is subclass of JWTError)
     - User not found: 401 (user was deleted after login)
  
  4. Why use Depends()?
     - Automatically runs before route handler
     - If dependency fails, route never runs
     - If dependency succeeds, passes result to route
""")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserDB:
    """
    Dependency: verify JWT and return current user.
    Used by Depends() on protected routes.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
    except JWTError:
        raise HTTPException(401, "Invalid token")
    
    user = db.query(UserDB).filter(UserDB.id == int(user_id)).first()
    if not user:
        raise HTTPException(401, "User not found")
    
    return user

@app.get("/api/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserDB = Depends(get_current_user)):
    """Protected route: requires valid JWT"""
    return current_user

print("✓ Protected routes implemented")

# ============================================================
# SECTION 6: TEST IT
# ============================================================

print("\n" + "-"*70)
print("SECTION 6: TEST THE FLOW")
print("-"*70)
print("""
Now test the complete flow:
  1. POST /auth/register → create user
  2. POST /auth/login → get JWT token
  3. GET /api/me with token → get user
  4. GET /api/me without token → 403 error
  5. Try with wrong password → 401 error

Commands:
  # Start this script
  python this_file.py
  
  # In another terminal
  curl -X POST http://localhost:8000/auth/register \\
    -H "Content-Type: application/json" \\
    -d '{"email":"alice@test.com","password":"SecurePass123"}'
  
  curl -X POST http://localhost:8000/auth/login \\
    -H "Content-Type: application/x-www-form-urlencoded" \\
    -d "username=alice@test.com&password=SecurePass123"
  
  TOKEN="..."  # from login response
  curl http://localhost:8000/api/me \\
    -H "Authorization: Bearer $TOKEN"
""")

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("WEEK 1 REVIEW RUNNING")
    print("="*70)
    print("\nServer starting on http://localhost:8000")
    print("API docs: http://localhost:8000/docs")
    print("\nTest the endpoints above!")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
