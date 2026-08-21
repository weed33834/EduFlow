"""学生画像路由"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.deps import get_current_user
from app.models import User, StudentProfile

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ProfileResponse(BaseModel):
    current_level: str
    learning_goal: str | None
    preferred_style: str
    strengths: list
    weaknesses: list
    total_study_minutes: int
    streak_days: int


class ProfileUpdate(BaseModel):
    learning_goal: str | None = None
    current_level: str | None = None
    preferred_style: str | None = None


@router.get("", response_model=ProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学生画像"""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return ProfileResponse(
        current_level=profile.current_level,
        learning_goal=profile.learning_goal,
        preferred_style=profile.preferred_style,
        strengths=profile.strengths or [],
        weaknesses=profile.weaknesses or [],
        total_study_minutes=profile.total_study_minutes,
        streak_days=profile.streak_days,
    )


@router.put("", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新学生画像"""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)

    if data.learning_goal is not None:
        profile.learning_goal = data.learning_goal
    if data.current_level is not None:
        profile.current_level = data.current_level
    if data.preferred_style is not None:
        profile.preferred_style = data.preferred_style

    await db.commit()
    await db.refresh(profile)

    return ProfileResponse(
        current_level=profile.current_level,
        learning_goal=profile.learning_goal,
        preferred_style=profile.preferred_style,
        strengths=profile.strengths or [],
        weaknesses=profile.weaknesses or [],
        total_study_minutes=profile.total_study_minutes,
        streak_days=profile.streak_days,
    )
