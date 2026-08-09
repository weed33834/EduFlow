from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.security import hash_password, verify_password, create_access_token
from core.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    display_name: str = ""


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
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
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
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
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
