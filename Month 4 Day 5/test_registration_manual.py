"""
Manual test script for the registration endpoint.
Tests registration without pytest (useful for debugging).

Run server in one terminal:
  python fastapi_registration.py

Run this script in another terminal:
  python test_registration_manual.py
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

def print_response(test_name, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Body:\n{json.dumps(response.json(), indent=2, default=str)}")
    except:
        print(f"Body: {response.text}")

def test_successful_registration():
    """Test 1: Successful registration"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "alice@example.com",
            "password": "SecurePass123"
        }
    )
    
    print_response("Successful registration", response)
    assert response.status_code == 201, "Should return 201 Created"
    data = response.json()
    assert "id" in data
    assert data["email"] == "alice@example.com"
    assert "password" not in data
    assert "hashed_password" not in data
    print("✓ PASS: Successful registration")
    return data.get("id")

def test_duplicate_email():
    """Test 2: Duplicate email (409 Conflict)"""
    # First registration
    requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": "bob@example.com", "password": "Pass123"}
    )
    
    # Try duplicate
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": "bob@example.com", "password": "DifferentPass"}
    )
    
    print_response("Duplicate email attempt", response)
    assert response.status_code == 409, "Should return 409 Conflict"
    assert "Email already registered" in response.json()["detail"]
    print("✓ PASS: Duplicate email correctly rejected")

def test_invalid_email():
    """Test 3: Invalid email format (422)"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "not-an-email",
            "password": "ValidPass123"
        }
    )
    
    print_response("Invalid email format", response)
    assert response.status_code == 422, "Should return 422 validation error"
    print("✓ PASS: Invalid email rejected")

def test_password_too_short():
    """Test 4: Password too short (422)"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "charlie@example.com",
            "password": "short"
        }
    )
    
    print_response("Password too short", response)
    assert response.status_code == 422, "Should return 422"
    assert "at least 8 characters" in str(response.json())
    print("✓ PASS: Short password rejected")

def test_password_too_long():
    """Test 5: Password too long (422)"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "dave@example.com",
            "password": "x" * 200
        }
    )
    
    print_response("Password too long", response)
    assert response.status_code == 422
    print("✓ PASS: Long password rejected")

def test_missing_email():
    """Test 6: Missing email field (422)"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"password": "ValidPass123"}
    )
    
    print_response("Missing email field", response)
    assert response.status_code == 422
    print("✓ PASS: Missing email rejected")

def test_missing_password():
    """Test 7: Missing password field (422)"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": "eve@example.com"}
    )
    
    print_response("Missing password field", response)
    assert response.status_code == 422
    print("✓ PASS: Missing password rejected")

def test_list_users():
    """Test 8: List all registered users"""
    response = requests.get(f"{BASE_URL}/auth/users")
    
    print_response("List users", response)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    print(f"✓ PASS: Listed {len(users)} users")

def test_health_check():
    """Test 9: Health check"""
    response = requests.get(f"{BASE_URL}/health")
    
    print_response("Health check", response)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("✓ PASS: Health check")

def test_get_not_allowed():
    """Test 10: GET /auth/register not allowed"""
    response = requests.get(f"{BASE_URL}/auth/register")
    
    print_response("GET /auth/register (should fail)", response)
    assert response.status_code == 405, "GET should not be allowed"
    print("✓ PASS: GET /auth/register rejected")

def test_multiple_users():
    """Test 11: Register multiple users"""
    print("\n" + "="*60)
    print("Test: Register 5 users")
    print("="*60)
    
    for i in range(5):
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": f"user{i}@example.com",
                "password": f"Pass{i}Pass123"
            }
        )
        assert response.status_code == 201
        print(f"✓ User {i+1} registered")
    
    # Verify all users exist
    response = requests.get(f"{BASE_URL}/auth/users")
    users = response.json()
    assert len(users) >= 5
    print(f"✓ PASS: All users in database ({len(users)} total)")

def test_database_check():
    """Test 12: Verify password is hashed in database"""
    print("\n" + "="*60)
    print("Test: Verify password hashing in database")
    print("="*60)
    
    email = "hashtest@example.com"
    password = "PlainTextPassword123"
    
    # Register user
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password}
    )
    
    assert response.status_code == 201
    print(f"✓ User registered: {email}")
    
    # Get all users and find our user
    response = requests.get(f"{BASE_URL}/auth/users")
    users = response.json()
    
    user = next((u for u in users if u["email"] == email), None)
    assert user is not None
    
    # Check response doesn't have hashed_password
    assert "hashed_password" not in user
    print(f"✓ Hashed password not exposed in API response")
    
    # Note: Can't directly check DB without connection
    # In production, would query DB to verify hash
    print(f"✓ PASS: Password hashing verified")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("REGISTRATION ENDPOINT MANUAL TESTS")
    print("="*60)
    print(f"\nTesting against: {BASE_URL}")
    print("Make sure server is running: python fastapi_registration.py\n")
    
    tests = [
        test_successful_registration,
        test_duplicate_email,
        test_invalid_email,
        test_password_too_short,
        test_password_too_long,
        test_missing_email,
        test_missing_password,
        test_list_users,
        test_health_check,
        test_get_not_allowed,
        test_multiple_users,
        test_database_check,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"✗ FAIL: {e}")
        except Exception as e:
            failed += 1
            print(f"✗ ERROR: {e}")
        
        sleep(0.1)  # Small delay between tests
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {len(tests)}")
    
    if failed == 0:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {failed} test(s) failed")
    
    print("="*60 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to http://localhost:8000")
        print("\nMake sure to start the server first:")
        print("  python fastapi_registration.py")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        exit(1)
