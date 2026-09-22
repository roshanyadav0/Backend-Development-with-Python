"""
Manual test script for login endpoint.
Tests registration → login → protected route flow.

Run server in one terminal:
  python fastapi_auth_complete.py

Run this script in another terminal:
  python test_login_manual.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_step(step_num, title):
    print(f"\n{'='*70}")
    print(f"Step {step_num}: {title}")
    print('='*70)

def print_response(status, body):
    print(f"Status: {status}")
    try:
        print(f"Body:\n{json.dumps(body, indent=2, default=str)}")
    except:
        print(f"Body: {body}")

def test_complete_flow():
    """Test: complete registration → login → protected route flow"""
    
    print_step(1, "REGISTER USER")
    
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "alice@example.com",
            "password": "SecurePass123"
        }
    )
    
    print_response(register_response.status_code, register_response.json())
    assert register_response.status_code == 201
    user_id = register_response.json()["id"]
    print(f"✓ User registered with ID: {user_id}")
    
    # ======================================
    print_step(2, "LOGIN WITH CORRECT PASSWORD")
    
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "alice@example.com",
            "password": "SecurePass123"
        }
    )
    
    print_response(login_response.status_code, login_response.json())
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    expires_in = login_response.json()["expires_in"]
    print(f"✓ Login successful")
    print(f"  Token (first 50 chars): {token[:50]}...")
    print(f"  Expires in: {expires_in} seconds (~{expires_in // 60} minutes)")
    
    # ======================================
    print_step(3, "ACCESS PROTECTED ROUTE WITH TOKEN")
    
    headers = {"Authorization": f"Bearer {token}"}
    protected_response = requests.get(
        f"{BASE_URL}/api/me",
        headers=headers
    )
    
    print_response(protected_response.status_code, protected_response.json())
    assert protected_response.status_code == 200
    user = protected_response.json()
    assert user["email"] == "alice@example.com"
    print(f"✓ Protected route accessed successfully")
    print(f"  User: {user['email']}")
    
    # ======================================
    print_step(4, "ACCESS PROTECTED ROUTE WITHOUT TOKEN")
    
    no_token_response = requests.get(f"{BASE_URL}/api/me")
    
    print_response(no_token_response.status_code, no_token_response.json())
    assert no_token_response.status_code == 403
    print(f"✓ Access denied without token (403)")
    
    # ======================================
    print_step(5, "TRY LOGIN WITH WRONG PASSWORD")
    
    wrong_pass_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "alice@example.com",
            "password": "WrongPassword456"
        }
    )
    
    print_response(wrong_pass_response.status_code, wrong_pass_response.json())
    assert wrong_pass_response.status_code == 401
    print(f"✓ Login rejected with wrong password (401)")
    
    # ======================================
    print_step(6, "TRY LOGIN WITH NON-EXISTENT EMAIL")
    
    not_found_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "anypassword"
        }
    )
    
    print_response(not_found_response.status_code, not_found_response.json())
    assert not_found_response.status_code == 401
    error = not_found_response.json()["detail"]
    assert "Incorrect email or password" in error
    print(f"✓ Generic error message prevents email enumeration")
    
    # ======================================
    print_step(7, "REGISTER SECOND USER AND LOGIN")
    
    requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": "bob@example.com",
            "password": "BobPass456"
        }
    )
    
    bob_login = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "bob@example.com",
            "password": "BobPass456"
        }
    )
    
    bob_token = bob_login.json()["access_token"]
    
    # Bob accesses his own profile
    bob_headers = {"Authorization": f"Bearer {bob_token}"}
    bob_response = requests.get(f"{BASE_URL}/api/profile", headers=bob_headers)
    
    print_response(bob_response.status_code, bob_response.json())
    assert bob_response.status_code == 200
    assert bob_response.json()["email"] == "bob@example.com"
    print(f"✓ Second user (bob@example.com) logged in successfully")
    
    # ======================================
    print_step(8, "VERIFY TOKENS ARE DIFFERENT")
    
    payload_alice = json.loads(
        json.dumps(requests.get(
            f"{BASE_URL}/api/me",
            headers={"Authorization": f"Bearer {token}"}
        ).json())
    )
    
    payload_bob = json.loads(
        json.dumps(requests.get(
            f"{BASE_URL}/api/me",
            headers={"Authorization": f"Bearer {bob_token}"}
        ).json())
    )
    
    assert payload_alice["email"] != payload_bob["email"]
    assert payload_alice["id"] != payload_bob["id"]
    print(f"✓ Each user gets unique token with their user ID")
    print(f"  Alice (token 1): ID={payload_alice['id']}, email={payload_alice['email']}")
    print(f"  Bob (token 2):   ID={payload_bob['id']}, email={payload_bob['email']}")

def test_login_multiple_times():
    """Test: same user can login multiple times, gets different tokens"""
    
    print_step(9, "SAME USER MULTIPLE LOGINS")
    
    # Register
    requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": "charlie@example.com", "password": "CharliePass789"}
    )
    
    # Login 3 times
    tokens = []
    for i in range(3):
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": "charlie@example.com",
                "password": "CharliePass789"
            }
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        tokens.append(token)
        print(f"  Login {i+1}: {token[:30]}...")
    
    # All tokens should be different (new token each time)
    assert len(set(tokens)) == 3
    print(f"✓ Same user gets different token on each login (3 logins, 3 unique tokens)")

def test_corrupted_token():
    """Test: corrupted token is rejected"""
    
    print_step(10, "CORRUPTED TOKEN")
    
    # Register and login
    requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": "dave@example.com", "password": "DavePass123"}
    )
    
    login = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "dave@example.com", "password": "DavePass123"}
    )
    
    token = login.json()["access_token"]
    
    # Corrupt the token
    corrupted = token[:-10] + "xxxxxxxxxx"
    
    # Try to use corrupted token
    response = requests.get(
        f"{BASE_URL}/api/me",
        headers={"Authorization": f"Bearer {corrupted}"}
    )
    
    assert response.status_code == 401
    print_response(response.status_code, response.json())
    print(f"✓ Corrupted token rejected (401)")

def main():
    print("\n" + "="*70)
    print("LOGIN ENDPOINT - COMPLETE FLOW TESTS")
    print("="*70)
    print(f"\nTesting against: {BASE_URL}")
    print("Make sure server is running: python fastapi_auth_complete.py\n")
    
    try:
        test_complete_flow()
        test_login_multiple_times()
        test_corrupted_token()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED")
        print("="*70)
        print("\n✓ Registration endpoint works")
        print("✓ Login endpoint works")
        print("✓ JWT tokens are issued correctly")
        print("✓ Protected routes require valid token")
        print("✓ Wrong password is rejected")
        print("✓ Non-existent email is rejected")
        print("✓ Corrupted tokens are rejected")
        print("✓ Multiple users can login independently")
        print("\n" + "="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to http://localhost:8000")
        print("\nMake sure to start the server first:")
        print("  python fastapi_auth_complete.py")
        exit(1)
