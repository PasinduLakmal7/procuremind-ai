import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import bcrypt
from jose import JWTError, jwt
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored bcrypt hash using bcrypt directly."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generates a secure bcrypt hash for a plaintext password using bcrypt directly."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(
    user_id: str,
    email: str,
    organization_id: str,
    roles: List[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generates a signed JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "organization_id": str(organization_id),
        "roles": roles,
        "token_type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str, datetime]:
    """Generates a signed JWT refresh token and returns (token, jti, expire_datetime)."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    jti = str(uuid.uuid4())
    to_encode: Dict[str, Any] = {
        "sub": str(user_id),
        "token_type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": jti,
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt, jti, expire
