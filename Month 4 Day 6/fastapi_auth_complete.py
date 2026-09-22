"""
FastAPI Auth: Complete registration + login system
Combines Days 5 (registration) and Day 6 (login + JWT)

Flow:
  1. POST /auth/register → store user with hashed password
  2. POST /auth/login → verify password, issue JWT token
  3. GET /api/me → protected route using token
"""

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, String, DateTime, Integer, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

# ============================================================
# CONFIGURATION
# ============================================================

DATABASE_URL = "sqlite:///./auth.db"
SECRET_KEY = "your-secret-key-keep-safe-min-32-chars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access tokens

# ============================================================
# DATABASE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserDB(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

Base.metadata.create_all(bind=engine)

# ============================================================
# PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class UserRegisterRequest(BaseModel):
    """Registration request"""
    email: EmailStr
    password: str
    
    @validator('password')
    def password_valid(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must be at most 128 characters')
        return v

class Token(BaseModel):
    """Login response"""
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    """JWT payload data"""
    sub: str  # user_id
    exp: datetime

class UserResponse(BaseModel):
    """User info (no password or hash)"""
    id: int
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(title="Auth API (Register + Login)", version="1.0")

# OAuth2 scheme for protected routes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# HELPERS
# ============================================================

def authenticate_user(email: str, password: str, db: Session) -> Optional[UserDB]:
    """
    Authenticate user:
    1. Find user by email
    2. Verify password hash (constant-time comparison)
    3. Return user or None
    """
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if not user:
        return None
    
    # ✓ CRITICAL: Use pwd_context.verify() for constant-time comparison
    # This prevents timing attacks that could leak password info
    if not pwd_context.verify(password, user.hashed_password):
        return None
    
    return user

def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> tuple[str, int]:
    """
    Create JWT access token.
    
    Returns: (token_string, expires_in_seconds)
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    payload = {
        "sub": str(user_id),  # subject = user ID
        "exp": expire,        # expiration
        "iat": datetime.utcnow()  # issued at
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # Return token and seconds until expiry
    expires_in = int((expire - datetime.utcnow()).total_seconds())
    return token, expires_in

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserDB:
    """
    Dependency: verify JWT and return current user.
    Used to protect routes.
    """
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credential_exception
    except JWTError:
        raise credential_exception
    
    # Fetch user from database
    user = db.query(UserDB).filter(UserDB.id == int(user_id)).first()
    if user is None:
        raise credential_exception
    
    return user

# ============================================================
# ENDPOINTS
# ============================================================

@app.post("/auth/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Validation:
      - Email format
      - Email uniqueness (409 if exists)
      - Password length (8-128 chars)
    
    Storage:
      - Hash password with bcrypt (automatic salt)
      - Store email + hash (never plain password)
    """
    # Check if email already exists
    existing = db.query(UserDB).filter(UserDB.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = pwd_context.hash(user_data.password)
    
    # Store user
    db_user = UserDB(email=user_data.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint.
    
    Flow:
      1. Accept form data (email/username, password)
      2. Find user in database by email
      3. Verify password against stored hash
      4. If valid: create JWT with 15-minute expiry
      5. Return token to client
    
    Errors:
      - 401: User not found or password incorrect
    
    Note: Uses generic 401 message to avoid leaking whether email exists.
    """
    # Step 1: Authenticate user
    # Using email from form (could be username if you store that)
    user = authenticate_user(form_data.username, form_data.password, db)
    
    if not user:
        # ✓ Generic error message: don't say "user not found" or "wrong password"
        # This prevents attackers from enumerating valid emails
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Step 2: Create JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token, expires_in = create_access_token(
        user_id=user.id,
        expires_delta=access_token_expires
    )
    
    # Step 3: Return token
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in
    }

@app.get("/api/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserDB = Depends(get_current_user)):
    """
    Protected endpoint: get current user's info.
    
    Requires:
      - Authorization header with valid JWT token
      - Token must not be expired
    
    Returns:
      - User info (no password or hash)
    """
    return current_user

@app.get("/api/profile")
async def get_profile(current_user: UserDB = Depends(get_current_user)):
    """Another protected route as example"""
    return {
        "email": current_user.email,
        "registered": current_user.created_at.isoformat(),
        "message": f"Welcome back, {current_user.email}!"
    }

@app.get("/health")
async def health_check():
    """Health check (no auth required)"""
    return {"status": "ok"}

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("FastAPI Complete Auth System (Register + Login + Protected Routes)")
    print("="*70)
    print(f"\nDatabase: {DATABASE_URL}")
    print("\n📝 Test Users (after registration):")
    print("  Email: alice@example.com | Password: SecurePass123")
    print("  Email: bob@example.com   | Password: AnotherPass456")
    print("\n🔑 Endpoints:")
    print("  POST   /auth/register    — Register new user")
    print("  POST   /auth/login       — Login, get JWT token")
    print("  GET    /api/me           — Current user (protected)")
    print("  GET    /api/profile      — User profile (protected)")
    print("  GET    /health           — Health check (public)")
    print("\n📚 Interactive docs: http://localhost:8000/docs")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
