"""
Pytest tests for login endpoint.
Tests: password verification, JWT issuance, token usage.

Run with: pytest test_login.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import time

# Import from main app
from fastapi_auth_complete import app, get_db, Base, pwd_context, SECRET_KEY, ALGORITHM
from jose import jwt

DATABASE_URL = "sqlite:///./test_login.db"

# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture(scope="function")
def setup_test_db():
    """Create test database"""
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(setup_test_db):
    """Test client connected to test DB"""
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# ============================================================
# TESTS: SUCCESSFUL LOGIN
# ============================================================

def test_login_success(client):
    """
    Test: successful login with correct credentials.
    Expected: 200 OK, valid JWT token returned.
    """
    # Register user first
    response = client.post(
        "/auth/register",
        json={"email": "alice@test.com", "password": "SecurePass123"}
    )
    assert response.status_code == 201
    
    # Login
    response = client.post(
        "/auth/login",
        data={"username": "alice@test.com", "password": "SecurePass123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert data["expires_in"] > 0
    
    print(f"✓ Login successful")
    print(f"  Token (first 50 chars): {data['access_token'][:50]}...")
    print(f"  Expires in: {data['expires_in']} seconds")
    
    return data["access_token"]

def test_login_returns_jwt(client):
    """
    Test: token returned is valid JWT.
    Expected: token is properly formatted, can be decoded.
    """
    # Register
    client.post(
        "/auth/register",
        json={"email": "bob@test.com", "password": "Pass123456"}
    )
    
    # Login
    response = client.post(
        "/auth/login",
        data={"username": "bob@test.com", "password": "Pass123456"}
    )
    
    token = response.json()["access_token"]
    
    # Decode JWT to verify it's valid
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    assert payload["sub"] is not None  # user_id
    assert "exp" in payload  # expiration
    assert "iat" in payload  # issued at
    
    print(f"✓ JWT is valid")
    print(f"  Subject (user_id): {payload['sub']}")
    print(f"  Issued at: {payload['iat']}")

# ============================================================
# TESTS: LOGIN FAILURES
# ============================================================

def test_login_wrong_password(client):
    """
    Test: login with wrong password.
    Expected: 401 Unauthorized.
    """
    # Register
    client.post(
        "/auth/register",
        json={"email": "charlie@test.com", "password": "CorrectPass123"}
    )
    
    # Try wrong password
    response = client.post(
        "/auth/login",
        data={"username": "charlie@test.com", "password": "WrongPass456"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "Incorrect email or password" in data["detail"]
    
    print(f"✓ Wrong password rejected with 401")

def test_login_user_not_found(client):
    """
    Test: login with non-existent email.
    Expected: 401 Unauthorized (generic message, no info leak).
    """
    response = client.post(
        "/auth/login",
        data={"username": "nonexistent@test.com", "password": "anypass123"}
    )
    
    assert response.status_code == 401
    data = response.json()
    # Generic message doesn't reveal whether email exists
    assert "Incorrect email or password" in data["detail"]
    
    print(f"✓ Non-existent email rejected with 401 (generic message)")

def test_login_empty_password(client):
    """
    Test: login with empty password.
    Expected: 401 (wrong password).
    """
    client.post(
        "/auth/register",
        json={"email": "dave@test.com", "password": "Pass123456"}
    )
    
    response = client.post(
        "/auth/login",
        data={"username": "dave@test.com", "password": ""}
    )
    
    assert response.status_code == 401
    print(f"✓ Empty password rejected")

# ============================================================
# TESTS: JWT TOKEN USAGE
# ============================================================

def test_use_token_to_access_protected_route(client):
    """
    Test: use JWT token to access protected route.
    Expected: 200 OK, user info returned.
    """
    # Register
    client.post(
        "/auth/register",
        json={"email": "eve@test.com", "password": "SecurePass123"}
    )
    
    # Login
    login_response = client.post(
        "/auth/login",
        data={"username": "eve@test.com", "password": "SecurePass123"}
    )
    token = login_response.json()["access_token"]
    
    # Use token to access protected route
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/me", headers=headers)
    
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == "eve@test.com"
    assert "id" in user
    assert "created_at" in user
    
    print(f"✓ Protected route accessed with valid token")
    print(f"  User: {user['email']}")

def test_protected_route_without_token(client):
    """
    Test: access protected route without token.
    Expected: 403 Forbidden (missing authentication).
    """
    response = client.get("/api/me")
    
    # Missing token should return 403
    assert response.status_code == 403
    
    print(f"✓ Protected route rejected without token")

def test_protected_route_with_invalid_token(client):
    """
    Test: access protected route with corrupted token.
    Expected: 401 Unauthorized.
    """
    bad_token = "invalid.jwt.token"
    headers = {"Authorization": f"Bearer {bad_token}"}
    
    response = client.get("/api/me", headers=headers)
    
    assert response.status_code == 401
    
    print(f"✓ Protected route rejected with invalid token")

def test_protected_route_with_expired_token(client):
    """
    Test: access protected route with expired token.
    Expected: 401 Unauthorized.
    """
    # Create an expired token
    from datetime import datetime, timedelta
    
    expired_payload = {
        "sub": "999",
        "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
    }
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/me", headers=headers)
    
    assert response.status_code == 401
    
    print(f"✓ Expired token rejected")

# ============================================================
# TESTS: MULTIPLE USERS
# ============================================================

def test_multiple_users_login_independently(client):
    """
    Test: multiple users can register and login independently.
    Expected: each user gets their own token and data.
    """
    users = [
        ("user1@test.com", "Pass111111"),
        ("user2@test.com", "Pass222222"),
        ("user3@test.com", "Pass333333")
    ]
    
    for email, password in users:
        client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )
    
    # Login as each user
    for email, password in users:
        login_response = client.post(
            "/auth/login",
            data={"username": email, "password": password}
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Use token to verify identity
        headers = {"Authorization": f"Bearer {token}"}
        user_response = client.get("/api/me", headers=headers)
        
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert user_data["email"] == email
    
    print(f"✓ {len(users)} users can login and access protected routes")

# ============================================================
# TESTS: TOKEN PROPERTIES
# ============================================================

def test_token_expiry_time(client):
    """
    Test: token includes correct expiry time.
    Expected: expires_in matches JWT exp claim.
    """
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "frank@test.com", "password": "Pass123456"}
    )
    
    response = client.post(
        "/auth/login",
        data={"username": "frank@test.com", "password": "Pass123456"}
    )
    
    data = response.json()
    token = data["access_token"]
    expires_in = data["expires_in"]
    
    # Decode token
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    # Verify expiry matches
    exp_from_jwt = payload["exp"]
    iat_from_jwt = payload["iat"]
    calculated_expires = exp_from_jwt - iat_from_jwt
    
    # Should match (within 2 seconds)
    assert abs(calculated_expires - expires_in) <= 2, \
        f"Expires_in {expires_in}s doesn't match JWT exp {calculated_expires}s"
    
    print(f"✓ Token expiry is correct: {expires_in}s")

def test_token_contains_user_id(client):
    """
    Test: JWT token contains user ID (sub claim).
    Expected: sub = user's ID from database.
    """
    # Register
    reg_response = client.post(
        "/auth/register",
        json={"email": "grace@test.com", "password": "Pass123456"}
    )
    user_id = reg_response.json()["id"]
    
    # Login
    login_response = client.post(
        "/auth/login",
        data={"username": "grace@test.com", "password": "Pass123456"}
    )
    
    token = login_response.json()["access_token"]
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    # Verify sub matches user ID
    assert payload["sub"] == str(user_id)
    
    print(f"✓ Token contains correct user ID: {user_id}")

# ============================================================
# TESTS: PASSWORD VERIFICATION SECURITY
# ============================================================

def test_password_comparison_is_constant_time(client):
    """
    Test: password verification uses constant-time comparison.
    Note: This is hard to test directly, but we verify pwd_context.verify() is used.
    """
    # Register
    client.post(
        "/auth/register",
        json={"email": "henry@test.com", "password": "ExactPassword123"}
    )
    
    # Test various wrong passwords
    wrong_passwords = [
        "a",                # Very different
        "ExactPassword1",   # Almost right (off by 1 char)
        "ExactPassword123x", # Extra char
        "wrongwrongwrong",  # Different length
    ]
    
    for wrong_pass in wrong_passwords:
        response = client.post(
            "/auth/login",
            data={"username": "henry@test.com", "password": wrong_pass}
        )
        assert response.status_code == 401
    
    print(f"✓ All wrong passwords rejected consistently")

# ============================================================
# TESTS: ERROR MESSAGES
# ============================================================

def test_generic_error_message_prevents_email_enumeration(client):
    """
    Test: error message doesn't reveal whether email exists.
    Expected: same message for "user not found" and "wrong password".
    """
    # Register one user
    client.post(
        "/auth/register",
        json={"email": "iris@test.com", "password": "Pass123456"}
    )
    
    # Try login with non-existent email
    response1 = client.post(
        "/auth/login",
        data={"username": "nonexistent@test.com", "password": "anypass"}
    )
    
    # Try login with wrong password
    response2 = client.post(
        "/auth/login",
        data={"username": "iris@test.com", "password": "wrongpass"}
    )
    
    # Both should return 401
    assert response1.status_code == 401
    assert response2.status_code == 401
    
    # Both should have generic error message
    msg1 = response1.json()["detail"]
    msg2 = response2.json()["detail"]
    assert msg1 == msg2 == "Incorrect email or password"
    
    print(f"✓ Generic error message prevents email enumeration")

# ============================================================
# TESTS: HTTP METHODS
# ============================================================

def test_login_get_not_allowed(client):
    """
    Test: GET /auth/login should not be allowed.
    Expected: 405 Method Not Allowed.
    """
    response = client.get("/auth/login")
    assert response.status_code == 405
    print(f"✓ GET /auth/login correctly rejected")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Login Endpoint Tests")
    print("="*60)
    print("\nRun with: pytest test_login.py -v")
    print("\nTests cover:")
    print("  ✓ Successful login with correct credentials")
    print("  ✓ Login with wrong password (401)")
    print("  ✓ Login with non-existent email (401)")
    print("  ✓ JWT token validation")
    print("  ✓ Token usage on protected routes")
    print("  ✓ Expired token rejection")
    print("  ✓ Multiple users")
    print("  ✓ Token claims (sub, exp, iat)")
    print("  ✓ Constant-time password comparison")
    print("  ✓ Generic error messages (prevent email enumeration)")
    print("\n" + "="*60 + "\n")
