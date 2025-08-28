import hashlib
import jwt
import datetime
import pytz
import psycopg2
from typing import Optional
from fastapi import HTTPException, status, Header
from config import settings
from database import get_db_connection

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.datetime.now(pytz.utc) + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def get_current_user_id(token: str = Header(None)) -> str:
    """Get the current user ID from the JWT token."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization token missing")
    payload = verify_token(token)
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return user_id

def authenticate_user(username: str, password: str) -> Optional[str]:
    """Authenticate a user with username and password."""
    conn = None
    try:
        conn = get_db_connection(settings.database_config)
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
        result = cur.fetchone()

        if result and result[1] == hash_password(password):
            return str(result[0])
        return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def create_user(username: str, password: str) -> Optional[str]:
    """Create a new user and return the user ID."""
    conn = None
    try:
        conn = get_db_connection(settings.database_config)
        cur = conn.cursor()
        password_hash = hash_password(password)
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id", (username, password_hash))
        user_id = cur.fetchone()[0]
        conn.commit()
        return str(user_id)
    except psycopg2.IntegrityError:
        # Username already exists
        return None
    except Exception as e:
        print(f"User creation error: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()
