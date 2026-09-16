from jose import jwt
from datetime import datetime, timedelta
import time

SECRET_KEY = "secret"

def create_token(expires_seconds: int):
    """Create a token that expires in N seconds"""
    now = datetime.utcnow()
    payload = {
        "sub": "user_789",
        "iat": now,
        "exp": now + timedelta(seconds=expires_seconds)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def check_token(token: str):
    """Try to verify the token"""
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return "✓ Valid"
    except jwt.ExpiredSignatureError:
        return "❌ Expired"
    except jwt.JWTError:
        return "❌ Invalid"


if __name__ == "__main__":
    print("=== Token Expiry Demo ===\n")
    
    # Create a token that expires in 3 seconds
    token = create_token(expires_seconds=3)
    print(f"Token created, expires in 3 seconds")
    print(f"Status: {check_token(token)}\n")
    
    print("Waiting 2 seconds...")
    time.sleep(2)
    print(f"Status: {check_token(token)}\n")
    
    print("Waiting 2 more seconds (total 4 > 3)...")
    time.sleep(2)
    print(f"Status: {check_token(token)}\n")
    
    print("---\n✓ Without expiry, a stolen token lives forever")
    print("✓ With 1-hour expiry, the attacker has a 1-hour window")
    print("✓ With refresh tokens, you can revoke access immediately")
