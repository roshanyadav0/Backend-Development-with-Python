"""
Pytest tests for refresh token pattern

Tests:
  - Login returns both access and refresh tokens
  - Refresh token can be used to get new access token
  - Expired access token can be refreshed
  - Revoked refresh token is rejected
  - Logout revokes all refresh tokens
  - Multiple concurrent refresh tokens per user

Run with: pytest test_refresh_tokens.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from jose import jwt

from fastapi_refresh_tokens import (
    app, get_db, Base, RefreshTokenDB, UserDB,
    SECRET_KEY, ALGORITHM
)

DATABASE_URL = "sqlite:///./test_refresh.db"

@pytest.fixture(scope="function")
def setup_test_db():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(setup_test_db):
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
# TESTS: LOGIN WITH REFRESH TOKENS
# ============================================================

def test_login_returns_both_tokens(client):
    """Test: login returns both access and refresh tokens"""
    print("\n" + "="*70)
    print("TEST: Login returns both tokens")
    print("="*70)
    
    # Register
    client.post(
        "/auth/register",
        json={"email": "alice@test.com", "password": "Pass123"}
    )
    
    # Login
    response = client.post(
        "/auth/login",
        data={"username": "alice@test.com", "password": "Pass123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check both tokens present
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    
    access = data["access_token"]
    refresh = data["refresh_token"]
    
    print(f"✓ Access token: {access[:50]}...")
    print(f"✓ Refresh token: {refresh[:50]}...")
    print(f"✓ Expires in: {data['expires_in']} seconds")
    
    # Verify tokens are different
    assert access != refresh
    
    # Verify token types
    access_payload = jwt.decode(access, SECRET_KEY, algorithms=[ALGORITHM])
    refresh_payload = jwt.decode(refresh, SECRET_KEY, algorithms=[ALGORITHM])
    
    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"
    
    print("✓ Token types correct")

# ============================================================
# TESTS: REFRESH TOKEN USAGE
# ============================================================

def test_refresh_token_gets_new_access_token(client):
    """Test: use refresh token to get new access token"""
    print("\n" + "="*70)
    print("TEST: Use refresh token to get new access token")
    print("="*70)
    
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "bob@test.com", "password": "Pass123"}
    )
    
    login = client.post(
        "/auth/login",
        data={"username": "bob@test.com", "password": "Pass123"}
    )
    
    refresh_token = login.json()["refresh_token"]
    
    print(f"Got refresh token: {refresh_token[:50]}...")
    
    # Use refresh token to get new access token
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check new access token
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    new_access = data["access_token"]
    print(f"✓ New access token: {new_access[:50]}...")
    
    # Verify it's valid
    payload = jwt.decode(new_access, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["type"] == "access"
    assert payload["sub"] == "1"
    
    print("✓ New access token is valid")

def test_use_new_access_token(client):
    """Test: new access token works on protected routes"""
    print("\n" + "="*70)
    print("TEST: New access token works on protected routes")
    print("="*70)
    
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "charlie@test.com", "password": "Pass123"}
    )
    
    login = client.post(
        "/auth/login",
        data={"username": "charlie@test.com", "password": "Pass123"}
    )
    
    refresh_token = login.json()["refresh_token"]
    
    # Get new access token
    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    new_access_token = refresh_response.json()["access_token"]
    print(f"Refreshed access token: {new_access_token[:50]}...")
    
    # Use new access token
    headers = {"Authorization": f"Bearer {new_access_token}"}
    response = client.get("/api/me", headers=headers)
    
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == "charlie@test.com"
    
    print(f"✓ Can access protected route with refreshed token")

# ============================================================
# TESTS: REFRESH TOKEN VALIDATION
# ============================================================

def test_invalid_refresh_token(client):
    """Test: invalid refresh token is rejected"""
    print("\n" + "="*70)
    print("TEST: Invalid refresh token rejected")
    print("="*70)
    
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid.fake.token"}
    )
    
    assert response.status_code == 401
    print("✓ Invalid token rejected (401)")

def test_wrong_token_type(client):
    """Test: using access token as refresh token fails"""
    print("\n" + "="*70)
    print("TEST: Access token cannot be used as refresh token")
    print("="*70)
    
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "dave@test.com", "password": "Pass123"}
    )
    
    login = client.post(
        "/auth/login",
        data={"username": "dave@test.com", "password": "Pass123"}
    )
    
    access_token = login.json()["access_token"]
    
    # Try to use access token as refresh token
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": access_token}
    )
    
    assert response.status_code == 401
    print("✓ Access token rejected as refresh token (401)")

def test_refresh_token_stored_in_db(client):
    """Test: refresh token is stored in database"""
    print("\n" + "="*70)
    print("TEST: Refresh token stored in database")
    print("="*70)
    
    from fastapi_refresh_tokens import SessionLocal
    
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "eve@test.com", "password": "Pass123"}
    )
    
    login = client.post(
        "/auth/login",
        data={"username": "eve@test.com", "password": "Pass123"}
    )
    
    # Check database
    db = SessionLocal()
    tokens = db.query(RefreshTokenDB).filter(RefreshTokenDB.user_id == 1).all()
    db.close()
    
    assert len(tokens) == 1
    token = tokens[0]
    
    assert token.user_id == 1
    assert token.token_id is not None
    assert token.token_hash is not None
    assert token.revoked_at is None  # Active
    assert not token.is_rotated  # Not rotated
    
    print(f"✓ Token stored in DB")
    print(f"  - token_id: {token.token_id}")
    print(f"  - expires_at: {token.expires_at}")
    print(f"  - revoked_at: {token.revoked_at} (None = active)")

# ============================================================
# TESTS: LOGOUT & REVOCATION
# ============================================================

def test_logout_revokes_refresh_tokens(client):
    """Test: logout revokes all refresh tokens"""
    print("\n" + "="*70)
    print("TEST: Logout revokes all refresh tokens")
    print("="*70)
    
    from fastapi_refresh_tokens import SessionLocal
    
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "frank@test.com", "password": "Pass123"}
    )
    
    login = client.post(
        "/auth/login",
        data={"username": "frank@test.com", "password": "Pass123"}
    )
    
    access_token = login.json()["access_token"]
    
    print("Before logout:")
    db = SessionLocal()
    tokens = db.query(RefreshTokenDB).filter(RefreshTokenDB.user_id == 1).all()
    print(f"  Active tokens: {len([t for t in tokens if t.revoked_at is None])}")
    db.close()
    
    # Logout
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/auth/logout", headers=headers)
    
    assert response.status_code == 200
    
    print("After logout:")
    db = SessionLocal()
    tokens = db.query(RefreshTokenDB).filter(RefreshTokenDB.user_id == 1).all()
    active = [t for t in tokens if t.revoked_at is None]
    print(f"  Active tokens: {len(active)}")
    assert len(active) == 0
    db.close()
    
    print("✓ All refresh tokens revoked")

def test_revoked_token_cannot_refresh(client):
    """Test: revoked refresh token cannot get new access token"""
    print("\n" + "="*70)
    print("TEST: Revoked refresh token cannot refresh")
    print("="*70)
    
    from fastapi_refresh_tokens import SessionLocal
    
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "grace@test.com", "password": "Pass123"}
    )
    
    login = client.post(
        "/auth/login",
        data={"username": "grace@test.com", "password": "Pass123"}
    )
    
    access_token = login.json()["access_token"]
    refresh_token = login.json()["refresh_token"]
    
    # Logout (revoke token)
    headers = {"Authorization": f"Bearer {access_token}"}
    client.post("/auth/logout", headers=headers)
    
    print("Token revoked via logout")
    
    # Try to use revoked token
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 401
    print("✓ Revoked token rejected (401)")

# ============================================================
# TESTS: MULTIPLE TOKENS PER USER
# ============================================================

def test_multiple_refresh_tokens_per_user(client):
    """Test: user can have multiple active refresh tokens"""
    print("\n" + "="*70)
    print("TEST: Multiple refresh tokens per user")
    print("="*70)
    
    from fastapi_refresh_tokens import SessionLocal
    
    # Register user
    client.post(
        "/auth/register",
        json={"email": "henry@test.com", "password": "Pass123"}
    )
    
    # Login 3 times (device 1, 2, 3)
    tokens = []
    for i in range(3):
        response = client.post(
            "/auth/login",
            data={"username": "henry@test.com", "password": "Pass123"}
        )
        refresh_token = response.json()["refresh_token"]
        tokens.append(refresh_token)
        print(f"  Login {i+1}: Got refresh token")
    
    # Check database
    db = SessionLocal()
    db_tokens = db.query(RefreshTokenDB).filter(RefreshTokenDB.user_id == 1).all()
    db.close()
    
    assert len(db_tokens) == 3
    print(f"✓ User has 3 refresh tokens (multiple devices)")
    
    # All tokens should work
    for i, refresh_token in enumerate(tokens):
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        print(f"  Token {i+1}: Can refresh ✓")

# ============================================================
# TESTS: TOKEN EXPIRY
# ============================================================

def test_expired_refresh_token_rejected(client):
    """Test: expired refresh token is rejected"""
    print("\n" + "="*70)
    print("TEST: Expired refresh token rejected")
    print("="*70)
    
    from fastapi_refresh_tokens import SessionLocal
    
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "iris@test.com", "password": "Pass123"}
    )
    
    login = client.post(
        "/auth/login",
        data={"username": "iris@test.com", "password": "Pass123"}
    )
    
    refresh_token = login.json()["refresh_token"]
    
    # Manually expire the token in database
    db = SessionLocal()
    db_token = db.query(RefreshTokenDB).filter(RefreshTokenDB.user_id == 1).first()
    db_token.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
    db.commit()
    db.close()
    
    print("Token manually expired in database")
    
    # Try to use expired token
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 401
    print("✓ Expired token rejected (401)")

# ============================================================
# TESTS: EDGE CASES
# ============================================================

def test_access_token_cannot_be_used_on_refresh_endpoint(client):
    """Test: access token is rejected on refresh endpoint"""
    print("\n" + "="*70)
    print("TEST: Access token rejected on refresh endpoint")
    print("="*70)
    
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "jack@test.com", "password": "Pass123"}
    )
    
    login = client.post(
        "/auth/login",
        data={"username": "jack@test.com", "password": "Pass123"}
    )
    
    access_token = login.json()["access_token"]
    
    # Try to use access token on refresh endpoint
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": access_token}
    )
    
    assert response.status_code == 401
    print("✓ Access token rejected on refresh endpoint (401)")

if __name__ == "__main__":
    print("""
Refresh Token Tests

Tests the complete refresh token pattern:
  - Login returns both tokens
  - Refresh token can get new access token
  - Revoked tokens are rejected
  - Logout revokes all tokens
  - Multiple tokens per user

Run with:
  pytest test_refresh_tokens.py -v
""")
