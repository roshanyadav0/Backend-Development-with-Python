"""
Week 1 Review: Edge Case Tests for JWT Security

Tests the 5 edge cases that can break authentication:
  1. Expired token
  2. Tampered signature
  3. Wrong secret key
  4. Missing required claim
  5. User deleted after login

Run with: pytest test_edge_cases.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt
from datetime import datetime, timedelta
from fastapi_auth_complete import app, get_db, Base

DATABASE_URL = "sqlite:///./test_edge_cases.db"

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
# EDGE CASE 1: EXPIRED TOKEN
# ============================================================

def test_edge_case_1_expired_token(client):
    """
    Edge Case 1: Token has expired (exp timestamp is in the past)
    
    Scenario:
      - User logged in 16 minutes ago
      - Token set to expire in 15 minutes
      - Token is now expired
    
    Expected:
      - 401 Unauthorized
      - Token rejected
    """
    print("\n" + "="*70)
    print("EDGE CASE 1: EXPIRED TOKEN")
    print("="*70)
    
    # Register a user (just to have an ID)
    client.post(
        "/auth/register",
        json={"email": "alice@test.com", "password": "Pass123"}
    )
    
    # Create an expired token manually
    from fastapi_auth_complete import SECRET_KEY, ALGORITHM
    
    expired_payload = {
        "sub": "1",
        "exp": datetime.utcnow() - timedelta(minutes=1),  # Expired 1 min ago
        "iat": datetime.utcnow() - timedelta(minutes=16)
    }
    
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    print(f"Created token that expired 1 minute ago")
    print(f"Token: {expired_token[:50]}...")
    
    # Try to use the expired token
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/me", headers=headers)
    
    print(f"Response: {response.status_code}")
    
    # Assertion
    assert response.status_code == 401, \
        f"Expected 401, got {response.status_code}"
    
    print("✓ PASS: Expired token rejected")

# ============================================================
# EDGE CASE 2: TAMPERED SIGNATURE
# ============================================================

def test_edge_case_2_tampered_signature(client):
    """
    Edge Case 2: Token signature has been modified/corrupted
    
    Scenario:
      - Valid token is issued
      - Attacker modifies last 10 characters of signature
      - Signature no longer matches payload
    
    Expected:
      - 401 Unauthorized
      - Signature verification fails
    """
    print("\n" + "="*70)
    print("EDGE CASE 2: TAMPERED SIGNATURE")
    print("="*70)
    
    # Register and login to get valid token
    client.post(
        "/auth/register",
        json={"email": "bob@test.com", "password": "Pass123"}
    )
    
    login = client.post(
        "/auth/login",
        data={"username": "bob@test.com", "password": "Pass123"}
    )
    
    valid_token = login.json()["access_token"]
    
    print(f"Valid token: {valid_token[:50]}...")
    
    # Tamper with signature (change last 10 chars)
    tampered_token = valid_token[:-10] + "xxxxxxxxxx"
    
    print(f"Tampered token: {tampered_token[:50]}...")
    print(f"Changed last 10 characters")
    
    # Try to use tampered token
    headers = {"Authorization": f"Bearer {tampered_token}"}
    response = client.get("/api/me", headers=headers)
    
    print(f"Response: {response.status_code}")
    
    # Assertion
    assert response.status_code == 401, \
        f"Expected 401, got {response.status_code}"
    
    print("✓ PASS: Tampered signature rejected")

# ============================================================
# EDGE CASE 3: WRONG SECRET KEY
# ============================================================

def test_edge_case_3_wrong_secret_key(client):
    """
    Edge Case 3: Token was signed with a different secret
    
    Scenario:
      - Attacker signs a token with wrong secret
      - Token structure is valid, but signature won't match
    
    Expected:
      - 401 Unauthorized
      - Signature verification fails (can't verify with correct secret)
    """
    print("\n" + "="*70)
    print("EDGE CASE 3: WRONG SECRET KEY")
    print("="*70)
    
    # Create token with wrong secret
    wrong_secret = "different-secret-key-not-the-real-one"
    
    payload = {
        "sub": "1",
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "iat": datetime.utcnow()
    }
    
    wrong_secret_token = jwt.encode(payload, wrong_secret, algorithm="HS256")
    
    print(f"Created token with wrong secret: '{wrong_secret}'")
    print(f"Token: {wrong_secret_token[:50]}...")
    
    # Try to use it (server will try to verify with correct secret)
    headers = {"Authorization": f"Bearer {wrong_secret_token}"}
    response = client.get("/api/me", headers=headers)
    
    print(f"Response: {response.status_code}")
    
    # Assertion
    assert response.status_code == 401, \
        f"Expected 401, got {response.status_code}"
    
    print("✓ PASS: Token with wrong secret rejected")

# ============================================================
# EDGE CASE 4: MISSING REQUIRED CLAIM
# ============================================================

def test_edge_case_4_missing_required_claim(client):
    """
    Edge Case 4: Token missing the 'sub' (subject/user_id) claim
    
    Scenario:
      - Token is created without user_id
      - Signature is valid (not tampered)
      - But required claim is missing
    
    Expected:
      - 401 Unauthorized
      - Can't identify user without 'sub' claim
    """
    print("\n" + "="*70)
    print("EDGE CASE 4: MISSING REQUIRED CLAIM")
    print("="*70)
    
    from fastapi_auth_complete import SECRET_KEY, ALGORITHM
    
    # Create token without 'sub' claim
    payload = {
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "iat": datetime.utcnow()
        # MISSING: "sub"
    }
    
    no_sub_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    print(f"Created token without 'sub' claim")
    print(f"Token payload: {payload}")
    print(f"Token: {no_sub_token[:50]}...")
    
    # Try to use it
    headers = {"Authorization": f"Bearer {no_sub_token}"}
    response = client.get("/api/me", headers=headers)
    
    print(f"Response: {response.status_code}")
    
    # Assertion
    assert response.status_code == 401, \
        f"Expected 401, got {response.status_code}"
    
    print("✓ PASS: Missing required claim rejected")

# ============================================================
# EDGE CASE 5: USER DELETED AFTER LOGIN
# ============================================================

def test_edge_case_5_user_deleted_after_login(client):
    """
    Edge Case 5: User logs in, gets token. Then user is deleted from DB.
    
    Scenario:
      - User registers and logs in
      - Admin deletes user from database
      - User tries to use their token
      - Token is still valid (not expired, signature correct)
      - But user doesn't exist in database
    
    Expected:
      - 401 Unauthorized
      - Token is valid, but user is gone
    """
    print("\n" + "="*70)
    print("EDGE CASE 5: USER DELETED AFTER LOGIN")
    print("="*70)
    
    from fastapi_auth_complete import SessionLocal, UserDB
    
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "charlie@test.com", "password": "Pass123"}
    )
    
    login = client.post(
        "/auth/login",
        data={"username": "charlie@test.com", "password": "Pass123"}
    )
    
    valid_token = login.json()["access_token"]
    
    print(f"User logged in successfully")
    print(f"Token: {valid_token[:50]}...")
    
    # Delete user from database (simulate admin action)
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.email == "charlie@test.com").first()
    db.delete(user)
    db.commit()
    db.close()
    
    print(f"User deleted from database")
    
    # Try to use the token (it's still valid from JWT perspective)
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = client.get("/api/me", headers=headers)
    
    print(f"Response: {response.status_code}")
    print(f"Token is still valid (not expired, correct signature)")
    print(f"But user doesn't exist in database")
    
    # Assertion
    assert response.status_code == 401, \
        f"Expected 401, got {response.status_code}"
    
    print("✓ PASS: Deleted user rejected (database lookup caught it)")

# ============================================================
# BONUS: VALID TOKEN STILL WORKS
# ============================================================

def test_bonus_valid_token_works(client):
    """
    Bonus test: Verify that valid tokens DO work
    
    This confirms our edge case tests aren't too strict.
    """
    print("\n" + "="*70)
    print("BONUS: VALID TOKEN WORKS")
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
    
    valid_token = login.json()["access_token"]
    
    print(f"Valid token: {valid_token[:50]}...")
    
    # Use valid token
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = client.get("/api/me", headers=headers)
    
    print(f"Response: {response.status_code}")
    
    # Assertion
    assert response.status_code == 200, \
        f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["email"] == "dave@test.com"
    
    print("✓ PASS: Valid token works correctly")

# ============================================================
# SUMMARY
# ============================================================

if __name__ == "__main__":
    print("""
Week 1 Review: Edge Case Tests

These tests verify that authentication properly rejects:
  1. Expired tokens
  2. Tampered signatures
  3. Tokens signed with wrong secret
  4. Tokens missing required claims
  5. Tokens for deleted users

Run with:
  pytest test_edge_cases.py -v

Expected result:
  6 PASSED (5 edge cases + 1 bonus)
""")
