"""
Test script for FastAPI JWT auth.
Shows how to:
  1. Login and get a token
  2. Use the token to access protected routes
  3. Handle expired/invalid tokens
"""

import requests
import json
import time
from datetime import datetime

# Server URL
BASE_URL = "http://localhost:8000"

def print_response(title, response):
    print(f"\n{title}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Body: {json.dumps(data, indent=2)}")
    except:
        print(f"Body: {response.text}")
    print("-" * 60)

def main():
    print("\n" + "="*60)
    print("FastAPI JWT Auth Test")
    print("="*60)
    
    # === Test 1: Public route (no auth) ===
    print("\n[TEST 1] Public route (no token needed)")
    response = requests.get(f"{BASE_URL}/api/public")
    print_response("GET /api/public", response)
    
    # === Test 2: Protected route without token (should fail) ===
    print("[TEST 2] Protected route WITHOUT token (should fail)")
    response = requests.get(f"{BASE_URL}/api/me")
    print_response("GET /api/me (no token)", response)
    
    # === Test 3: Invalid credentials (should fail) ===
    print("[TEST 3] Login with WRONG password (should fail)")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "alice", "password": "wrongpassword"}
    )
    print_response("POST /auth/login (wrong password)", response)
    
    # === Test 4: Valid login ===
    print("[TEST 4] Login with CORRECT credentials")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "alice", "password": "alice"}
    )
    print_response("POST /auth/login (alice)", response)
    
    if response.status_code != 200:
        print("❌ Login failed, skipping protected route tests")
        return
    
    token_data = response.json()
    token = token_data["access_token"]
    expires_in = token_data["expires_in"]
    
    print(f"\n✓ Token obtained!")
    print(f"  Token (first 50 chars): {token[:50]}...")
    print(f"  Expires in: {expires_in} seconds")
    
    # === Test 5: Protected route WITH valid token ===
    print("\n[TEST 5] Protected route WITH valid token")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/me", headers=headers)
    print_response("GET /api/me (with valid token)", response)
    
    # === Test 6: Another protected route ===
    print("[TEST 6] Another protected route WITH valid token")
    response = requests.get(f"{BASE_URL}/api/profile", headers=headers)
    print_response("GET /api/profile (with valid token)", response)
    
    # === Test 7: Token with typo (should fail) ===
    print("[TEST 7] Protected route with CORRUPTED token (should fail)")
    bad_token = token[:-10] + "xxxxxxxxxx"  # Change last 10 chars
    headers = {"Authorization": f"Bearer {bad_token}"}
    response = requests.get(f"{BASE_URL}/api/me", headers=headers)
    print_response("GET /api/me (corrupted token)", response)
    
    # === Test 8: Login as different user ===
    print("[TEST 8] Login as different user (bob)")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "bob", "password": "bob"}
    )
    bob_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {bob_token}"}
    response = requests.get(f"{BASE_URL}/api/me", headers=headers)
    print_response("GET /api/me (bob's token)", response)
    
    print("\n" + "="*60)
    print("✓ All tests completed!")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to http://localhost:8000")
        print("\nStart the server first:")
        print("  python fastapi_jwt_app.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
