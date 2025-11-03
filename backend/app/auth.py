# auth.py
"""
Authentication utilities:
- JWT token generation and verification
- Password hashing and verification
"""
from datetime import datetime, timedelta
from jose import jwt, JWTError
from werkzeug.security import generate_password_hash as werkzeug_hash
from werkzeug.security import check_password_hash as werkzeug_check
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# ========== JWT Token Functions ==========

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Generate JWT access token
    
    Args:
        data: Dictionary with user info (user_id, email)
        expires_delta: Optional custom expiration time
    
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Payload dictionary if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# ========== Password Hashing Functions ==========

def hash_password(password: str) -> str:
    """
    Hash a plain text password using PBKDF2-SHA256
    
    Args:
        password: Plain text password from user
    
    Returns:
        Hashed password string (safe to store in database)
    
    Example:
        hashed = hash_password("mySecurePassword123")
        # Returns: "pbkdf2:sha256:600000$salt$hash..."
    """
    return werkzeug_hash(password, method='pbkdf2:sha256', salt_length=16)

def verify_password(stored_hash: str, provided_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        stored_hash: Hashed password from database
        provided_password: Plain text password from user login
    
    Returns:
        True if password matches, False otherwise
    
    Example:
        is_valid = verify_password(user.password, "mySecurePassword123")
        if is_valid:
            # Login successful
    """
    return werkzeug_check(stored_hash, provided_password)
