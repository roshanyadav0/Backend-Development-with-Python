# FastAPI OAuth2PasswordBearer + JWT Authentication

Complete working example of JWT auth in FastAPI with OAuth2.

## Files

- **fastapi_jwt_app.py** — The main FastAPI app with all routes
- **test_fastapi_auth.py** — Automated test script (curl equiv)
- **FASTAPI_JWT_GUIDE.md** — Reference guide & common mistakes
- **jwt_example.py** — Day 2 JWT signing/verification (from earlier)
- **jwt_rs256.py** — Day 2 RSA asymmetric signing example
- **jwt_expiry.py** — Day 2 token expiry demo

## Setup (one time)

```bash
pip install fastapi uvicorn python-jose[cryptography] pydantic requests
```

## Running the Server

```bash
python fastapi_jwt_app.py
```

You'll see:
```
============================================================
FastAPI JWT Auth Server
============================================================

📝 Test users:
  Username: alice  |  Password: alice
  Username: bob    |  Password: bob

🔗 API Docs: http://localhost:8000/docs
📚 ReDoc: http://localhost:8000/redoc

============================================================
```

## Usage Options

### Option 1: Swagger UI (easiest)

1. Open http://localhost:8000/docs
2. Click on a route
3. Click "Try it out"
4. For protected routes:
   - Click the lock icon (🔒)
   - Click "Authorize"
   - First, login at POST /auth/login with username/password
   - Copy the access_token from the response
   - Paste into the Authorize dialog
   - Click "Authorize"
   - Now use protected routes

### Option 2: Manual curl tests

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=alice" | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Use token
curl http://localhost:8000/api/me \
  -H "Authorization: Bearer $TOKEN"

# 3. Public route (no token)
curl http://localhost:8000/api/public
```

### Option 3: Python test script

```bash
# Terminal 1: Start server
python fastapi_jwt_app.py

# Terminal 2: Run tests (waits for server)
python test_fastapi_auth.py
```

## Key Concepts Demonstrated

### OAuth2PasswordBearer
```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
```
- Extracts token from `Authorization: Bearer <token>` header
- Auto-generates Swagger UI "Authorize" button
- Returns 401 if token missing

### Login Endpoint
```python
@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm gives username, password, scope
    user = authenticate_user(form_data.username, form_data.password)
    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}
```

### Dependency Injection
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency: validates token, returns user
    FastAPI calls this before the route handler
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401)
    return get_user(username)

@app.get("/api/me")
async def read_me(current_user: User = Depends(get_current_user)):
    # get_current_user runs automatically
    # If token invalid → 401 (never reaches this function)
    # If token valid → current_user is the user object
    return current_user
```

## Routes

### Public (no auth)
- `GET /api/public` — Anyone can access

### Protected (token required)
- `POST /auth/login` — Login, get token (form data: username, password)
- `GET /api/me` — Current user data
- `GET /api/profile` — User profile

## Test Flow

```
1. POST /auth/login
   Input: username=alice, password=alice
   Output: {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 1800}

2. GET /api/me
   Header: Authorization: Bearer eyJ...
   Output: {"username": "alice", "full_name": "Alice Smith", "email": "alice@example.com"}
   
3. GET /api/public
   (no auth needed)
   Output: {"message": "This is a public route..."}
```

## What Happens Inside

### Login Flow
```
Client sends: POST /auth/login {username: "alice", password: "alice"}
     ↓
Server: authenticate_user("alice", "alice")
     ↓
Server: create_access_token({"sub": "alice"})
     ↓
Server: jwt.encode(
    {"sub": "alice", "exp": 1234567890},
    SECRET_KEY,
    algorithm="HS256"
)
     ↓
Client receives: {"access_token": "eyJhbGc...", "token_type": "bearer"}
```

### Protected Route Flow
```
Client sends: GET /api/me
             Header: Authorization: Bearer eyJhbGc...
     ↓
FastAPI: extract token from header (OAuth2PasswordBearer)
     ↓
FastAPI: call get_current_user(token="eyJhbGc...")
     ↓
get_current_user: jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
     ↓
Signature check: HMAC("eyJhbGc" + ".payload", SECRET_KEY) == signature
     ↓
If valid:   return User(username="alice", ...)
If invalid: raise HTTPException(401)
     ↓
If 401: Client receives 401 + error
If OK:  Route handler receives current_user, returns 200 + data
```

## Security Notes

⚠️ **This is a learning example. For production:**
- Use `bcrypt` instead of plain-text password comparison
- Store real users in a database (not FAKE_USERS_DB)
- Use HTTPS (token in Authorization header isn't encrypted by default)
- Rotate SECRET_KEY regularly
- Implement refresh tokens (separate long-lived token for getting new access tokens)
- Add password reset & account lockout
- Log auth failures
- Use environment variables for SECRET_KEY (not hardcoded)

## Troubleshooting

**"Connection refused"** → Server not running
- `python fastapi_jwt_app.py` in another terminal

**"Could not validate credentials"** → Token expired or invalid
- Login again to get a fresh token
- Check that the full token is being sent (including `Bearer ` prefix)

**"Incorrect username or password"** → Bad creds
- Use `alice` / `alice` or `bob` / `bob`
- Password must match the username (see authenticate_user function)

**Swagger UI "Authorize" button doesn't work** → Token already expired
- Click the lock again, login fresh
- Or test the /auth/login route first to get a new token

## Next: Day 4 Topics

- Refresh tokens (long-lived, stored on server, used to get new access tokens)
- Token blacklist (revoke tokens before expiry)
- Scopes & permissions (fine-grained access control)
- Role-based access control (RBAC)
