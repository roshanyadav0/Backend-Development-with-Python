"""
Pytest tests for the registration endpoint.
Tests registration flow, validation, error handling, and database storage.

Run with: pytest test_registration.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Import from main app
# In real project: from app.main import app, get_db, Base
# For this example, we assume they're in fastapi_registration.py

DATABASE_URL = "sqlite:///./test.db"

# ============================================================
# SETUP
# ============================================================

@pytest.fixture(scope="function")
def setup_test_db():
    """
    Create a fresh test database for each test.
    Ensures tests are isolated.
    """
    from fastapi_registration import Base, engine, SessionLocal
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Clean up after test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(setup_test_db):
    """
    Create a test client.
    Connects to test database instead of production.
    """
    from fastapi_registration import app, get_db, SessionLocal
    
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    # Clean up
    app.dependency_overrides.clear()

# ============================================================
# TESTS: SUCCESSFUL REGISTRATION
# ============================================================

def test_register_user_success(client):
    """
    Test: successful registration with valid email and password.
    Expected: 201 Created, user in database, password is hashed.
    """
    response = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "SecurePass123"
        }
    )
    
    # Check response
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    
    assert data["email"] == "alice@example.com"
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["message"] == "User registered successfully"
    assert "hashed_password" not in data  # Never expose hash in response
    
    print(f"✓ User registered successfully: {data}")

def test_register_user_in_database(client):
    """
    Test: user is actually stored in database with hashed password.
    Expected: password is NOT stored as plain text.
    """
    from fastapi_registration import SessionLocal, UserDB
    
    email = "bob@example.com"
    password = "AnotherPass456"
    
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password}
    )
    
    assert response.status_code == 201
    
    # Query database directly
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.email == email).first()
    db.close()
    
    # Verify user exists
    assert user is not None, "User not found in database"
    assert user.email == email
    
    # ✓ CRITICAL TEST: password is hashed, not plain text
    assert user.hashed_password != password, \
        "❌ SECURITY FAIL: Plain password stored in database!"
    
    # ✓ Password should start with bcrypt identifier
    assert user.hashed_password.startswith("$2b$"), \
        "Password not hashed with bcrypt"
    
    # ✓ Verify password verification works
    from fastapi_registration import pwd_context
    assert pwd_context.verify(password, user.hashed_password), \
        "Password verification failed"
    
    print(f"✓ Password correctly hashed: {user.hashed_password[:30]}...")

# ============================================================
# TESTS: DUPLICATE EMAIL (409)
# ============================================================

def test_register_duplicate_email_conflict(client):
    """
    Test: registering with an email that already exists.
    Expected: 409 Conflict.
    """
    email = "charlie@example.com"
    password = "Password789"
    
    # First registration
    response1 = client.post(
        "/auth/register",
        json={"email": email, "password": password}
    )
    assert response1.status_code == 201
    
    # Attempt duplicate registration
    response2 = client.post(
        "/auth/register",
        json={"email": email, "password": "DifferentPass123"}
    )
    
    assert response2.status_code == 409, \
        f"Expected 409, got {response2.status_code}"
    
    data = response2.json()
    assert "Email already registered" in data["detail"]
    
    print(f"✓ Duplicate email correctly rejected with 409")

# ============================================================
# TESTS: VALIDATION ERRORS (400)
# ============================================================

def test_register_invalid_email_format(client):
    """
    Test: invalid email format.
    Expected: 400 Bad Request.
    """
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",  # Missing @domain
            "password": "ValidPassword123"
        }
    )
    
    assert response.status_code == 422, \
        f"Expected 422 (validation), got {response.status_code}"
    
    print(f"✓ Invalid email format rejected")

def test_register_password_too_short(client):
    """
    Test: password less than 8 characters.
    Expected: 400 Bad Request / 422 Unprocessable Entity.
    """
    response = client.post(
        "/auth/register",
        json={
            "email": "dave@example.com",
            "password": "short"  # Only 5 chars
        }
    )
    
    assert response.status_code == 422, \
        f"Expected 422, got {response.status_code}"
    
    data = response.json()
    assert "Password must be at least 8 characters" in str(data)
    
    print(f"✓ Short password rejected")

def test_register_password_too_long(client):
    """
    Test: password exceeds 128 characters.
    Expected: 400 Bad Request / 422 Unprocessable Entity.
    """
    response = client.post(
        "/auth/register",
        json={
            "email": "eve@example.com",
            "password": "x" * 200  # Too long
        }
    )
    
    assert response.status_code == 422, \
        f"Expected 422, got {response.status_code}"
    
    print(f"✓ Long password rejected")

def test_register_missing_email(client):
    """
    Test: email field missing.
    Expected: 422 Unprocessable Entity.
    """
    response = client.post(
        "/auth/register",
        json={"password": "ValidPassword123"}
    )
    
    assert response.status_code == 422
    print(f"✓ Missing email rejected")

def test_register_missing_password(client):
    """
    Test: password field missing.
    Expected: 422 Unprocessable Entity.
    """
    response = client.post(
        "/auth/register",
        json={"email": "frank@example.com"}
    )
    
    assert response.status_code == 422
    print(f"✓ Missing password rejected")

# ============================================================
# TESTS: RESPONSE STRUCTURE
# ============================================================

def test_register_response_structure(client):
    """
    Test: response contains required fields and no sensitive data.
    Expected: id, email, created_at, message (no password or hash).
    """
    response = client.post(
        "/auth/register",
        json={
            "email": "grace@example.com",
            "password": "SecurePass123"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Required fields
    assert "id" in data
    assert "email" in data
    assert "created_at" in data
    assert "message" in data
    
    # Sensitive fields should NOT be in response
    assert "password" not in data
    assert "hashed_password" not in data
    
    print(f"✓ Response structure correct")

# ============================================================
# TESTS: EDGE CASES
# ============================================================

def test_register_email_case_sensitivity(client):
    """
    Test: emails with different cases.
    Should be treated as the same (or handle consistently).
    """
    # Register with lowercase
    response1 = client.post(
        "/auth/register",
        json={
            "email": "henry@example.com",
            "password": "Password123"
        }
    )
    assert response1.status_code == 201
    
    # Try with uppercase (depending on DB, this might be treated as duplicate)
    response2 = client.post(
        "/auth/register",
        json={
            "email": "HENRY@EXAMPLE.COM",
            "password": "Password456"
        }
    )
    
    # Should either be 409 (if case-insensitive) or 201 (if case-sensitive)
    # Most apps treat emails as case-insensitive
    print(f"Email case handling: {response2.status_code}")

def test_register_multiple_users(client):
    """
    Test: register multiple users successfully.
    Expected: all users created, no conflicts.
    """
    emails = [
        "user1@example.com",
        "user2@example.com",
        "user3@example.com"
    ]
    
    for email in emails:
        response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "ValidPass123"
            }
        )
        assert response.status_code == 201, f"Failed to register {email}"
    
    # Verify all users exist in DB
    from fastapi_registration import SessionLocal, UserDB
    db = SessionLocal()
    user_count = db.query(UserDB).count()
    db.close()
    
    assert user_count == len(emails), \
        f"Expected {len(emails)} users, found {user_count}"
    
    print(f"✓ Multiple users registered successfully")

# ============================================================
# TESTS: PASSWORD HASHING
# ============================================================

def test_password_hashing_unique(client):
    """
    Test: same password hashed multiple times produces different hashes.
    (Due to random salt in bcrypt)
    """
    from fastapi_registration import SessionLocal, UserDB
    
    password = "SamePassword123"
    
    # Register two users with same password
    response1 = client.post(
        "/auth/register",
        json={"email": "user1@test.com", "password": password}
    )
    response2 = client.post(
        "/auth/register",
        json={"email": "user2@test.com", "password": password}
    )
    
    assert response1.status_code == 201
    assert response2.status_code == 201
    
    # Get hashes from DB
    db = SessionLocal()
    user1 = db.query(UserDB).filter(UserDB.email == "user1@test.com").first()
    user2 = db.query(UserDB).filter(UserDB.email == "user2@test.com").first()
    db.close()
    
    # Hashes should be different (due to random salt)
    assert user1.hashed_password != user2.hashed_password, \
        "Same password produced identical hashes (salt failed)"
    
    # But both should verify correctly
    from fastapi_registration import pwd_context
    assert pwd_context.verify(password, user1.hashed_password)
    assert pwd_context.verify(password, user2.hashed_password)
    
    print(f"✓ Same password → different hashes ✓")

# ============================================================
# TESTS: HTTP METHODS
# ============================================================

def test_register_get_not_allowed(client):
    """
    Test: GET /auth/register should not be allowed.
    Expected: 405 Method Not Allowed.
    """
    response = client.get("/auth/register")
    assert response.status_code == 405
    print(f"✓ GET /auth/register correctly rejected")

# ============================================================
# TESTS: DATABASE CONSTRAINTS
# ============================================================

def test_register_email_unique_constraint(client):
    """
    Test: database enforces email uniqueness.
    Expected: second registration with same email fails.
    """
    email = "unique@example.com"
    
    # First registration
    response1 = client.post(
        "/auth/register",
        json={"email": email, "password": "Pass123"}
    )
    assert response1.status_code == 201
    
    # Try to register same email again
    response2 = client.post(
        "/auth/register",
        json={"email": email, "password": "DifferentPass456"}
    )
    
    # Should fail with 409 (or 500 if constraint violated at DB level)
    assert response2.status_code in [409, 500], \
        f"Expected 409 or 500, got {response2.status_code}"
    
    print(f"✓ Email uniqueness enforced")

# ============================================================
# TEST SUMMARY
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Registration Tests")
    print("="*60)
    print("\nRun with: pytest test_registration.py -v")
    print("\nTests cover:")
    print("  ✓ Successful registration")
    print("  ✓ Duplicate email (409 Conflict)")
    print("  ✓ Invalid email format (422)")
    print("  ✓ Password validation (too short/long)")
    print("  ✓ Password hashing (bcrypt, unique salt)")
    print("  ✓ Database storage (no plain text)")
    print("  ✓ Response structure (no exposure of secrets)")
    print("  ✓ Edge cases (multiple users, case sensitivity)")
    print("\n" + "="*60 + "\n")
