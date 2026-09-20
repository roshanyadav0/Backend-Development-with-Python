"""
FastAPI with secure password hashing.
Updated from Day 3 to use hashed passwords instead of plain text.

Key changes from Day 3:
  1. Import and setup CryptContext for password hashing
  2. Update User model to store hashed_password
  3. Hash password at signup
  4. Verify password at login (don't compare plain text)
  5. Never expose hashed password in API responses
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

# === PASSWORD HASHING ===
# In production: pip install passlib[bcrypt]
# For now, we'll show the pattern
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=12  # Slow by design: ~100ms per hash
    )
    BCRYPT_AVAILABLE = True
except ImportError:
    print("⚠️  passlib not installed. Using mock hashing for demo.")
    BCRYPT_AVAILABLE = False
    
    class MockContext:
        """Fallback for demo (DO NOT USE IN PRODUCTION)"""
        def hash(self, password: str) -> str:
            return f"hashed_{password}"
        
        def verify(self, plain: str, hashed: str) -> bool:
            return f"hashed_{plain}" == hashed
    
    pwd_context = MockContext()

# === JWT CONFIG ===
SECRET_KEY = "your-secret-key-keep-safe-min-32-chars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# === MODELS ===
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    """Public user model (never expose hashed_password)"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    """Internal model with hashed password (not in API responses)"""
    hashed_password: str

# === DATABASE ===
# Simulating a real database with hashed passwords
USERS_DB = {
    "alice": UserInDB(
        username="alice",
        full_name="Alice Smith",
        email="alice@example.com",
        hashed_password=pwd_context.hash("alice123"),  # ✓ HASHED!
        disabled=False
    ),
    "bob": UserInDB(
        username="bob",
        full_name="Bob Jones",
        email="bob@example.com",
        hashed_password=pwd_context.hash("qwerty99"),  # ✓ HASHED!
        disabled=False
    )
}

print("\n" + "="*60)
print("User Database (with hashed passwords)")
print("="*60)
for username, user in USERS_DB.items():
    print(f"\n{username}:")
    print(f"  Email: {user.email}")
    print(f"  Hash: {user.hashed_password[:30]}...")

# === FASTAPI APP ===
app = FastAPI(title="FastAPI Secure Auth", version="1.0")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ===== HELPERS =====

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate user:
    1. Find user in database
    2. Verify password against hashed value
    3. Never compare plain text passwords
    """
    if username not in USERS_DB:
        return None
    
    user = USERS_DB[username]
    
    # ✓ CORRECT: Use pwd_context.verify() to compare
    # This is constant-time, resists timing attacks
    if not pwd_context.verify(password, user.hashed_password):
        return None
    
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token"""
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
    except JWTError:
        raise credential_exception
    
    if username not in USERS_DB:
        raise credential_exception
    
    user = USERS_DB[username]
    return User(**user.dict(exclude={"hashed_password"}))  # ✓ NEVER expose hash!

# ===== ROUTES =====

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint.
    
    Key secure patterns:
      1. Authenticate: pwd_context.verify() against hashed password
      2. Never expose hashed_password in response
      3. Return only access_token (not password or hash)
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token, expires = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }

@app.post("/auth/signup")
async def signup(username: str, password: str, email: str, full_name: str = ""):
    """
    Signup endpoint.
    
    Secure password handling:
      1. Hash password: pwd_context.hash(password)
      2. Store hash in database (NEVER store plain password)
      3. Never return password or hash in response
    """
    if username in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # ✓ CORRECT: Hash password before storing
    hashed_password = pwd_context.hash(password)
    
    # ✓ Store hashed password in database
    new_user = UserInDB(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        disabled=False
    )
    USERS_DB[username] = new_user
    
    # ✓ Never return password or hash
    return {
        "username": new_user.username,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "message": "Signup successful! You can now login."
    }

@app.get("/api/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Protected route: returns current user.
    Note: current_user never includes hashed_password (excluded in get_current_user)
    """
    return current_user

@app.get("/api/public")
async def read_public():
    """Public route"""
    return {"message": "This is public"}

# ===== MAIN =====
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("FastAPI Secure Authentication")
    print("="*60)
    print(f"\n✓ Using: {'Bcrypt' if BCRYPT_AVAILABLE else 'Mock'} for password hashing")
    print("\nTest users:")
    print("  alice / alice123")
    print("  bob / qwerty99")
    print("\n📚 API Docs: http://localhost:8000/docs")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
