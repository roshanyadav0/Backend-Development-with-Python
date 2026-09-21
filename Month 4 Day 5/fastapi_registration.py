"""
FastAPI Registration Endpoint with SQLAlchemy ORM
Complete example: validation → hashing → storage → error handling
"""

from fastapi import FastAPI, HTTPException, status
from sqlalchemy import create_engine, Column, String, DateTime, Integer, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
from datetime import datetime
from typing import Optional

# ============================================================
# DATABASE SETUP
# ============================================================

# For local testing, use SQLite. For production, use PostgreSQL:
# DATABASE_URL = "postgresql://user:password@localhost/authdb"
DATABASE_URL = "sqlite:///./auth.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================================
# PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

# ============================================================
# DATABASE MODEL
# ============================================================

class UserDB(Base):
    """Database model for users (SQLAlchemy ORM)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

# Create tables
Base.metadata.create_all(bind=engine)

# ============================================================
# PYDANTIC MODELS (API schemas)
# ============================================================

class UserRegisterRequest(BaseModel):
    """Request schema for registration"""
    email: EmailStr  # Validates email format
    password: str
    
    @validator('password')
    def password_valid(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must be at most 128 characters')
        # Could add more checks: uppercase, digits, etc.
        return v

class UserResponse(BaseModel):
    """Response schema (never expose hashed_password)"""
    id: int
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserRegisterResponse(UserResponse):
    """Response after successful registration"""
    message: str = "User registered successfully"

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(title="Auth Registration API", version="1.0")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# ENDPOINTS
# ============================================================

@app.post(
    "/auth/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Flow:
      1. Validate input (email format, password length)
      2. Check if email already exists
      3. Hash password
      4. Store in database
      5. Return created user
    
    Errors:
      - 400: Invalid input (email format, password too short)
      - 409: Email already exists
      - 500: Database error
    """
    
    # Step 1: Check if email already exists
    existing_user = db.query(UserDB).filter(UserDB.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Step 2: Hash password (NEVER store plain text)
    hashed_password = pwd_context.hash(user_data.password)
    
    # Step 3: Create user in database
    db_user = UserDB(
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)  # Reload from DB to get ID and timestamps
    except Exception as e:
        db.rollback()
        print(f"Database error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Step 4: Return created user (with message, 201 status)
    return UserRegisterResponse(
        id=db_user.id,
        email=db_user.email,
        created_at=db_user.created_at,
        message="User registered successfully"
    )

@app.get("/auth/users", response_model=list[UserResponse])
async def list_users(db: Session = Depends(get_db)):
    """
    List all users (for testing/debugging only).
    Remove this in production.
    """
    users = db.query(UserDB).all()
    return users

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("FastAPI Registration API")
    print("="*60)
    print(f"\nDatabase: {DATABASE_URL}")
    print("\nEndpoints:")
    print("  POST   /auth/register    — Register a new user")
    print("  GET    /auth/users       — List all users (debug only)")
    print("  GET    /health           — Health check")
    print("\n📚 API Docs: http://localhost:8000/docs")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
