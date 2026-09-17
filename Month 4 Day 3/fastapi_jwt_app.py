from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

# === Configuration ===
SECRET_KEY = "your-secret-key-keep-safe-and-long-minimum-32-chars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# === Database (fake) ===
FAKE_USERS_DB = {
    "alice": {"username": "alice", "full_name": "Alice Smith", "email": "alice@example.com", "hashed_password": "fake-hash-alice", "disabled": False},
    "bob": {"username": "bob", "full_name": "Bob Jones", "email": "bob@example.com", "hashed_password": "fake-hash-bob", "disabled": False},
}

# === Models ===
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

# === FastAPI App ===
app = FastAPI(title="FastAPI JWT Auth", version="1.0")

# === OAuth2 Scheme ===
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# === Helper: verify password (fake) ===
def verify_password(plain_password, hashed_password):
    # In production, use bcrypt or similar
    return plain_password == hashed_password.replace("fake-hash-", "")

# === Helper: authenticate user ===
def authenticate_user(username: str, password: str):
    if username not in FAKE_USERS_DB:
        return False
    user = FAKE_USERS_DB[username]
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

# === Helper: create access token ===
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire

# === Dependency: get current user ===
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency that validates the JWT token and returns the current user.
    Automatically called on any route that depends on it.
    Rejects requests with no token or invalid token.
    """
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
        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception
    
    user = FAKE_USERS_DB.get(token_data.username)
    if user is None:
        raise credential_exception
    
    return User(**user)

# ===== ROUTES =====

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint.
    Accepts username and password (form data).
    Returns a JWT access token.
    
    OAuth2PasswordRequestForm expects:
      - username
      - password
      - (optional) scope
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token with 30-minute expiry
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token, expires = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
    }

@app.get("/api/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Protected route: returns current user data.
    
    Depends(get_current_user) automatically:
      1. Extracts the Authorization header
      2. Validates the JWT
      3. Returns the user object
      4. Rejects requests with missing/invalid token (401)
    """
    return current_user

@app.get("/api/profile")
async def read_profile(current_user: User = Depends(get_current_user)):
    """
    Another protected route showing how to use the current user.
    """
    return {
        "message": f"Hello {current_user.full_name}",
        "username": current_user.username,
        "email": current_user.email,
    }

@app.get("/api/public")
async def read_public():
    """
    Public route: no authentication required.
    """
    return {"message": "This is a public route, anyone can access it"}

# === Main ===
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("FastAPI JWT Auth Server")
    print("="*60)
    print("\n📝 Test users:")
    print("  Username: alice  |  Password: alice")
    print("  Username: bob    |  Password: bob")
    print("\n🔗 API Docs: http://localhost:8000/docs")
    print("📚 ReDoc: http://localhost:8000/redoc")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
