from jose import jwt
from datetime import datetime, timedelta
import json

# === Configuration ===
SECRET_KEY = "your-secret-key-keep-this-safe-min-32-chars"
ALGORITHM = "HS256"

# === Generate a JWT ===
def create_token(user_id: str, expires_hours: int = 1):
    now = datetime.utcnow()
    expires = now + timedelta(hours=expires_hours)
    
    payload = {
        "sub": user_id,           # subject (user ID)
        "iat": now,               # issued at
        "exp": expires,           # expiration time
        "iss": "my-app",          # issuer
        "role": "admin"           # custom claim
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


# === Verify and decode a JWT ===
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("❌ Token has expired")
        return None
    except jwt.JWTError as e:
        print(f"❌ Invalid token: {e}")
        return None


# === Example usage ===
if __name__ == "__main__":
    # Create a token
    token = create_token("user_456", expires_hours=1)
    print("Generated token:")
    print(token[:50] + "...\n")
    
    # Decode (without verification, just to see what's in it)
    parts = token.split(".")
    import base64
    payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)  # Add padding
    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    print("Payload (readable by anyone):")
    print(json.dumps(payload, indent=2, default=str))
    print()
    
    # Verify the token
    decoded = verify_token(token)
    if decoded:
        print("✓ Token is valid")
        print(f"  User ID: {decoded['sub']}")
        print(f"  Role: {decoded['role']}")
        print(f"  Expires: {datetime.fromtimestamp(decoded['exp'])}")
    
    # Try to verify a tampered token
    print("\n--- Testing tampered token ---")
    tampered = token[:-5] + "xxxxx"  # Change last 5 chars
    verify_token(tampered)
