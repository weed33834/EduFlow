from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import jwt
from core.config import settings

# 生产环境禁止使用默认密钥，防止 JWT 可被伪造
_DEFAULT_SECRET = "eduflow-secret-key-change-in-production"
if settings.ENV == "production" and settings.SECRET_KEY == _DEFAULT_SECRET:
    raise RuntimeError(
        "SECRET_KEY 仍为默认值，生产环境必须通过环境变量显式设置强随机密钥。"
    )


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode a JWT token. Raises JWTError on invalid token."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
