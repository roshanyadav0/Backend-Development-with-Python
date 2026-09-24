"""
Day 8: Refresh Token Pattern
Short-lived access tokens + long-lived refresh tokens

Flow:
  1. POST /auth/login → access_token (15 min) + refresh_token (7 days)
  2. Use access_token for API calls
  3. After 15 min, access_token expires
  4. POST /auth/refresh with refresh_token → new access_token
  5. Repeat step 2-4 until refresh_token expires (7 days)

Benefits:
  ✓ If access_token is stolen, window is only 15 minutes
  ✓ If refresh_token is stolen, can revoke it immediately
  ✓ Refresh_token can be rotated (old token invalidated on use)
"""

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, String, DateTime, Integer, func, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import uuid

# ============================================================
# CONFIGURATION
# ============================================================

DATABASE_URL = "sqlite:///./auth_refresh.db"
SECRET_KEY = "your-secret-key-keep-safe-min-32-chars"
ALGORITHM = "HS256"

# Token lifetimes
ACCESS_TOKEN_EXPIRE_MINUTES = 15          # Short-lived
REFRESH_TOKEN_EXPIRE_DAYS = 7             # Long-lived

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

class RefreshTokenDB(Base):
    """Refresh token model
    
    Why store refresh tokens in database?
      - Can revoke tokens (logout)
      - Can track token rotation
      - Can set expiry in database too (redundant but safe)
      - Can store token ID for audit logging
    """
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    token_id = Column(String, unique=True, nullable=False)  # jti (JWT ID)
    token_hash = Column(String, nullable=False)  # Never store plain token
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime, nullable=True)  # NULL = active, NOT NULL = revoked
    is_rotated = Column(Boolean, default=False)  # True if new token issued
    
    def is_valid(self) -> bool:
        """Check if token is valid (not revoked, not expired)"""
        now = datetime.utcnow()
        return (
            self.revoked_at is None and
            self.expires_at > now and
            not self.is_rotated
        )

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
# SCHEMAS
# ============================================================

class Token(BaseModel):
    """Login response with both tokens"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int  # access token expiry in seconds

class RefreshTokenRequest(BaseModel):
    """Refresh endpoint request"""
    refresh_token: str

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def password_valid(cls, v):
        if len(v) < 8:
            raise ValueError('Min 8 chars')
        return v

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(title="Auth with Refresh Tokens", version="1.0")
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

def hash_token(token: str) -> str:
    """Hash token before storing (treat like password)"""
    return pwd_context.hash(token)

def verify_token_hash(plain_token: str, hashed_token: str) -> bool:
    """Verify token hash"""
    return pwd_context.verify(plain_token, hashed_token)

def create_access_token(user_id: int) -> tuple[str, int]:
    """Create short-lived access token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    expires_in = int((expire - datetime.utcnow()).total_seconds())
    return token, expires_in

def create_refresh_token(user_id: int, db: Session) -> str:
    """Create long-lived refresh token and store in database"""
    # Generate unique token ID
    token_id = str(uuid.uuid4())
    
    # Create token payload
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": token_id,  # JWT ID for tracking
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    # Sign token
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # Store token hash in database (never store plain token)
    token_hash = hash_token(token)
    
    db_token = RefreshTokenDB(
        user_id=user_id,
        token_id=token_id,
        token_hash=token_hash,
        expires_at=expire
    )
    db.add(db_token)
    db.commit()
    
    return token

def verify_refresh_token(token: str, db: Session) -> Optional[int]:
    """
    Verify refresh token.
    Returns user_id if valid, None otherwise.
    """
    try:
        # Decode JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check type
        if payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        token_id = payload.get("jti")
        
        if not user_id or not token_id:
            return None
        
        # Check database
        db_token = db.query(RefreshTokenDB).filter(
            RefreshTokenDB.token_id == token_id
        ).first()
        
        if not db_token or not db_token.is_valid():
            return None
        
        return int(user_id)
        
    except JWTError:
        return None

def authenticate_user(email: str, password: str, db: Session):
    """Authenticate user by email and password"""
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Verify access token and return user"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check type
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
            
    except JWTError:
        raise HTTPException(401, "Invalid token")
    
    user = db.query(UserDB).filter(UserDB.id == int(user_id)).first()
    if not user:
        raise HTTPException(401, "User not found")
    
    return user

# ============================================================
# ENDPOINTS
# ============================================================

@app.post("/auth/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    existing = db.query(UserDB).filter(UserDB.email == user_data.email).first()
    if existing:
        raise HTTPException(409, "Email already registered")
    
    hashed = pwd_context.hash(user_data.password)
    db_user = UserDB(email=user_data.email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint.
    
    Returns both access and refresh tokens.
    """
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(401, "Incorrect email or password")
    
    # Create tokens
    access_token, expires_in = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id, db)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": expires_in
    }

@app.post("/auth/refresh", response_model=Token)
async def refresh(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh endpoint.
    
    Accepts refresh token, returns new access token.
    
    Optional: Rotate refresh token (invalidate old, issue new)
    """
    # Verify refresh token
    user_id = verify_refresh_token(request.refresh_token, db)
    if not user_id:
        raise HTTPException(401, "Invalid or expired refresh token")
    
    # Create new access token
    access_token, expires_in = create_access_token(user_id)
    
    # Optional: Rotate refresh token (invalidate old, issue new)
    # Uncomment to enable token rotation
    # try:
    #     payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    #     old_token_id = payload.get("jti")
    #     db_token = db.query(RefreshTokenDB).filter(
    #         RefreshTokenDB.token_id == old_token_id
    #     ).first()
    #     if db_token:
    #         db_token.is_rotated = True
    #         db.commit()
    # except:
    #     pass
    # 
    # new_refresh_token = create_refresh_token(user_id, db)
    # refresh_token_to_return = new_refresh_token
    
    # For now, just return same refresh token
    refresh_token_to_return = request.refresh_token
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_to_return,
        "token_type": "bearer",
        "expires_in": expires_in
    }

@app.post("/auth/logout")
async def logout(current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Logout endpoint.
    
    Revokes all refresh tokens for user.
    """
    db.query(RefreshTokenDB).filter(
        RefreshTokenDB.user_id == current_user.id,
        RefreshTokenDB.revoked_at.is_(None)
    ).update({"revoked_at": datetime.utcnow()})
    db.commit()
    
    return {"message": "Logged out successfully"}

@app.get("/api/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserDB = Depends(get_current_user)):
    """Protected route: requires valid access token"""
    return current_user

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("FastAPI Auth with Refresh Tokens")
    print("="*70)
    print("""
Endpoints:
  POST   /auth/register     — Register new user
  POST   /auth/login        — Login, get access + refresh tokens
  POST   /auth/refresh      — Use refresh token to get new access token
  POST   /auth/logout       — Revoke all refresh tokens
  GET    /api/me            — Protected (requires access token)
  GET    /health            — Health check

Flow:
  1. POST /auth/login → get access_token (15 min) + refresh_token (7 days)
  2. Use access_token for API calls
  3. After 15 min, access_token expires
  4. POST /auth/refresh (with refresh_token) → new access_token
  5. Repeat step 2-4 until refresh_token expires

Database:
  - users: email, hashed_password
  - refresh_tokens: token_id, token_hash, expires_at, revoked_at, is_rotated

📚 API Docs: http://localhost:8000/docs
""")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
