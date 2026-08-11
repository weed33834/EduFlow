from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from collections import defaultdict, deque
from datetime import datetime, timezone
from core.database import get_db
from core.security import hash_password, verify_password, create_access_token
from core.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 简单的内存限流：防止对登录/注册接口的暴力破解。
# key = "ip:email"，窗口内超限返回 429。生产多实例可替换为 Redis 实现。
_LOGIN_WINDOW_SECONDS = 60
_LOGIN_MAX_ATTEMPTS = 5
_REGISTER_MAX_ATTEMPTS = 3
_attempts: dict[str, deque] = defaultdict(deque)


def _check_rate_limit(key: str, max_attempts: int) -> None:
    now = datetime.now(timezone.utc).timestamp()
    q = _attempts[key]
    while q and now - q[0] > _LOGIN_WINDOW_SECONDS:
        q.popleft()
    if len(q) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="操作过于频繁，请稍后再试",
        )
    q.append(now)


def _client_key(request: Request, identity: str) -> str:
    ip = request.client.host if request.client else "unknown"
    return f"{ip}:{identity.lower()}"

# 用户名允许的字符：字母、数字、下划线、点、短横线，3-32 位
_USERNAME_RE = r"^[A-Za-z0-9_.-]{3,32}$"


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    display_name: str = ""

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if "@" not in v:
            raise ValueError("邮箱格式不正确")
        return v

    @field_validator("username")
    @classmethod
    def _validate_username(cls, v: str) -> str:
        import re

        v = (v or "").strip()
        if not re.fullmatch(_USERNAME_RE, v):
            raise ValueError("用户名需为 3-32 位字母、数字、下划线、点或短横线")
        return v

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少 8 位")
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("密码必须同时包含字母和数字")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class UpdateUserRequest(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def _user_dict(user: User) -> dict:
    """Return complete user information as a dictionary."""
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    _check_rate_limit(_client_key(request, req.email), _REGISTER_MAX_ATTEMPTS)
    # Check for duplicate email or username
    existing = await db.execute(
        select(User).where((User.email == req.email) | (User.username == req.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already exists",
        )

    user = User(
        email=req.email,
        username=req.username,
        hashed_password=hash_password(req.password),
        display_name=req.display_name or req.username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(access_token=token, user=_user_dict(user))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    _check_rate_limit(_client_key(request, req.email), _LOGIN_MAX_ATTEMPTS)
    result = await db.execute(select(User).where(User.email == req.email.strip().lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(access_token=token, user=_user_dict(user))


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return _user_dict(current_user)


@router.put("/me")
async def update_me(
    req: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.display_name is not None:
        current_user.display_name = req.display_name
    if req.avatar_url is not None:
        current_user.avatar_url = req.avatar_url
    if req.bio is not None:
        current_user.bio = req.bio

    await db.commit()
    await db.refresh(current_user)
    return _user_dict(current_user)
