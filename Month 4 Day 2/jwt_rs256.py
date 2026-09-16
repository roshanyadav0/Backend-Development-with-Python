from jose import jwt
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import json

# === Generate RSA key pair ===
def generate_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem


# === Issue token (server that owns the private key) ===
def create_token_rs256(private_key_pem: bytes, user_id: str):
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iss": "auth-server",
        "role": "user"
    }
    
    token = jwt.encode(payload, private_key_pem, algorithm="RS256")
    return token


# === Verify token (any server with the public key) ===
def verify_token_rs256(token: str, public_key_pem: bytes):
    try:
        payload = jwt.decode(token, public_key_pem, algorithms=["RS256"])
        return payload
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        return None
    except jwt.JWTError as e:
        print(f"❌ Invalid token: {e}")
        return None


if __name__ == "__main__":
    print("=== RS256: Asymmetric Signing ===\n")
    
    # Generate keys once (in production: keep private key secret, distribute public key)
    private_key, public_key = generate_keys()
    print("✓ Generated RSA key pair")
    print(f"  Private key size: {len(private_key)} bytes")
    print(f"  Public key size: {len(public_key)} bytes\n")
    
    # === Scenario 1: Auth server issues a token ===
    print("--- Auth Server (issues token) ---")
    token = create_token_rs256(private_key, "alice_123")
    print(f"Issued token: {token[:40]}...\n")
    
    # === Scenario 2: API server verifies the token ===
    print("--- API Server 1 (verifies with public key) ---")
    payload = verify_token_rs256(token, public_key)
    if payload:
        print(f"✓ User {payload['sub']} verified")
        print(f"  Expires: {datetime.fromtimestamp(payload['exp'])}\n")
    
    # === Scenario 3: Another API server (also has public key) ===
    print("--- API Server 2 (same public key, verifies independently) ---")
    payload = verify_token_rs256(token, public_key)
    if payload:
        print(f"✓ User {payload['sub']} verified\n")
    
    # === Scenario 4: Attacker tries to tamper ===
    print("--- Attacker tries to change role ---")
    tampered = token[:-10] + "xxxxxxx123"  # Corrupt signature
    verify_token_rs256(tampered, public_key)
