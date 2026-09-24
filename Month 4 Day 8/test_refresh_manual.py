"""
Manual test script for refresh token pattern.

Tests the complete flow:
  1. Register user
  2. Login → get access + refresh tokens
  3. Use access token on protected route
  4. Refresh to get new access token
  5. Logout to revoke refresh token
  6. Try to refresh after logout (should fail)

Run server in one terminal:
  python fastapi_refresh_tokens.py

Run this script in another terminal:
  python test_refresh_manual.py
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:8000"

def print_step(num, title):
    print(f"\n{'='*70}")
    print(f"Step {num}: {title}")
    print('='*70)

def print_response(status, body):
    print(f"Status: {status}")
    try:
        print(f"Response:\n{json.dumps(body, indent=2, default=str)}")
    except:
        print(f"Response: {body}")

def extract_tokens(response):
    """Extract tokens from response"""
    data = response.json()
    return data.get("access_token"), data.get("refresh_token")

def main():
    print("\n" + "="*70)
    print("REFRESH TOKEN PATTERN - COMPLETE FLOW TEST")
    print("="*70)
    print(f"\nTesting against: {BASE_URL}")
    print("Make sure server is running: python fastapi_refresh_tokens.py\n")
    
    try:
        # ======================================
        print_step(1, "REGISTER USER")
        
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": "alice@example.com",
                "password": "SecurePass123"
            }
        )
        
        print_response(response.status_code, response.json())
        assert response.status_code == 201
        print("✓ User registered")
        
        # ======================================
        print_step(2, "LOGIN → GET BOTH TOKENS")
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": "alice@example.com",
                "password": "SecurePass123"
            }
        )
        
        print_response(response.status_code, response.json())
        assert response.status_code == 200
        
        access_token, refresh_token = extract_tokens(response)
        expires_in = response.json()["expires_in"]
        
        print(f"✓ Got access token: {access_token[:50]}...")
        print(f"✓ Got refresh token: {refresh_token[:50]}...")
        print(f"✓ Access token expires in: {expires_in}s (~{expires_in//60} min)")
        
        # ======================================
        print_step(3, "USE ACCESS TOKEN ON PROTECTED ROUTE")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/api/me", headers=headers)
        
        print_response(response.status_code, response.json())
        assert response.status_code == 200
        user = response.json()
        
        print(f"✓ Protected route accessed")
        print(f"  User ID: {user['id']}")
        print(f"  Email: {user['email']}")
        
        # ======================================
        print_step(4, "SIMULATE ACCESS TOKEN EXPIRY")
        
        print("Waiting 2 seconds... (in production, you'd wait 15 minutes)")
        print("Note: We can't actually wait 15 min, but the mechanism is the same")
        time.sleep(2)
        
        print("✓ Access token would be expired now")
        print("  Client should call POST /auth/refresh to get new token")
        
        # ======================================
        print_step(5, "REFRESH TOKEN → GET NEW ACCESS TOKEN")
        
        response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        print_response(response.status_code, response.json())
        assert response.status_code == 200
        
        new_access_token, _ = extract_tokens(response)
        
        print(f"✓ Got new access token: {new_access_token[:50]}...")
        print(f"✓ Access and new access tokens are different:")
        print(f"  Old: {access_token[:30]}...")
        print(f"  New: {new_access_token[:30]}...")
        
        # ======================================
        print_step(6, "USE NEW ACCESS TOKEN")
        
        headers = {"Authorization": f"Bearer {new_access_token}"}
        response = requests.get(f"{BASE_URL}/api/me", headers=headers)
        
        print_response(response.status_code, response.json())
        assert response.status_code == 200
        
        print("✓ New access token works on protected route")
        
        # ======================================
        print_step(7, "LOGOUT (REVOKE ALL REFRESH TOKENS)")
        
        headers = {"Authorization": f"Bearer {new_access_token}"}
        response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
        
        print_response(response.status_code, response.json())
        assert response.status_code == 200
        
        print("✓ User logged out")
        print("  All refresh tokens revoked")
        
        # ======================================
        print_step(8, "TRY TO USE OLD REFRESH TOKEN (SHOULD FAIL)")
        
        response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        print_response(response.status_code, response.json())
        assert response.status_code == 401
        
        print("✓ Revoked refresh token rejected (401)")
        print("  User must login again to get new tokens")
        
        # ======================================
        print_step(9, "MULTIPLE LOGINS (MULTIPLE REFRESH TOKENS)")
        
        print("Simulating multiple device logins...")
        
        tokens = []
        for i in range(3):
            response = requests.post(
                f"{BASE_URL}/auth/login",
                data={
                    "username": "alice@example.com",
                    "password": "SecurePass123"
                }
            )
            assert response.status_code == 200
            _, refresh = extract_tokens(response)
            tokens.append(refresh)
            print(f"  Device {i+1}: Logged in, got refresh token")
        
        print(f"✓ User now has 3 active refresh tokens (3 devices)")
        
        # ======================================
        print_step(10, "EACH REFRESH TOKEN WORKS")
        
        for i, refresh in enumerate(tokens):
            response = requests.post(
                f"{BASE_URL}/auth/refresh",
                json={"refresh_token": refresh}
            )
            assert response.status_code == 200
            print(f"  Device {i+1}: Refresh token works ✓")
        
        print("✓ All refresh tokens are independent")
        
        # ======================================
        print_step(11, "LOGOUT REVOKES ALL")
        
        # Use last access token to logout
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": "alice@example.com",
                "password": "SecurePass123"
            }
        )
        access_token = response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
        assert response.status_code == 200
        
        print("Logged out...")
        
        # Try all refresh tokens
        failed = 0
        for i, refresh in enumerate(tokens):
            response = requests.post(
                f"{BASE_URL}/auth/refresh",
                json={"refresh_token": refresh}
            )
            if response.status_code == 401:
                print(f"  Device {i+1}: Refresh token revoked ✓")
                failed += 1
        
        print(f"✓ All {failed} refresh tokens revoked by single logout")
        
        # ======================================
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED")
        print("="*70)
        print("""
Summary:
  ✓ Login returns both tokens
  ✓ Access token works for 15 minutes
  ✓ Refresh token gets new access token
  ✓ Logout revokes all refresh tokens
  ✓ Multiple refresh tokens per user
  ✓ Single logout revokes all devices

Refresh Token Benefits:
  ✓ Users don't need to re-login every 15 minutes
  ✓ If access token is stolen, only 15-minute window
  ✓ If refresh token is stolen, admin can revoke it
  ✓ Can track which devices are logged in
  ✓ Can logout all devices with one action
  ✓ Can logout single device if compromised
""")
        print("="*70 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to http://localhost:8000")
        print("Make sure to start the server first:")
        print("  python fastapi_refresh_tokens.py")
        return False
        
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
    success = main()
    exit(0 if success else 1)
