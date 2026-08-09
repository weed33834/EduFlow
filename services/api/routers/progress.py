from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.deps import get_current_user
from models.user import User
from models.learning import Progress, Module, LearningPath

router = APIRouter(prefix="/api/progress", tags=["progress"])


class ProgressUpdate(BaseModel):
    module_id: int
    learning_time_minutes: int | None = None
    completion_percentage: float | None = None
    quiz_scores: list | None = None
    weak_points: list[str] | None = None
    strong_points: list[str] | None = None


@router.get("/me")
async def get_my_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Progress).where(Progress.user_id == current_user.id)
    )
    records = result.scalars().all()

    # Fetch module titles for each progress record
    details = []
    for r in records:
        module_title = None
        if r.module_id:
            mod_result = await db.execute(
                select(Module).where(Module.id == r.module_id)
            )
            module = mod_result.scalar_one_or_none()
            if module:
                module_title = module.title
        details.append(
            {
                "id": r.id,
                "module_id": r.module_id,
                "module_title": module_title,
                "learning_time_minutes": r.learning_time_minutes,
                "completion_percentage": r.completion_percentage,
                "quiz_scores": r.quiz_scores,
                "weak_points": r.weak_points,
                "strong_points": r.strong_points,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
        )

    return {
        "user_id": current_user.id,
        "module_count": len(records),
        "details": details,
    }


@router.post("/update")
async def update_progress(
    req: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify module ownership
    mod_result = await db.execute(
        select(Module).where(Module.id == req.module_id)
    )
    module = mod_result.scalar_one_or_none()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Module not found"
        )
    path_result = await db.execute(
        select(LearningPath).where(LearningPath.id == module.path_id)
    )
    path = path_result.scalar_one_or_none()
    if not path or path.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your module"
        )

    # Find or create progress record
    result = await db.execute(
        select(Progress).where(
            Progress.user_id == current_user.id,
            Progress.module_id == req.module_id,
        )
    )
    progress = result.scalar_one_or_none()

    if progress is None:
        progress = Progress(
            user_id=current_user.id,
            module_id=req.module_id,
            learning_time_minutes=0,
            completion_percentage=0.0,
            quiz_scores=[],
            weak_points=[],
            strong_points=[],
        )
        db.add(progress)

    if req.learning_time_minutes is not None:
        progress.learning_time_minutes = req.learning_time_minutes
    if req.completion_percentage is not None:
        progress.completion_percentage = req.completion_percentage
    if req.quiz_scores is not None:
        progress.quiz_scores = req.quiz_scores
    if req.weak_points is not None:
        progress.weak_points = req.weak_points
    if req.strong_points is not None:
        progress.strong_points = req.strong_points

    await db.commit()
    await db.refresh(progress)

    return {
        "id": progress.id,
        "user_id": progress.user_id,
        "module_id": progress.module_id,
        "learning_time_minutes": progress.learning_time_minutes,
        "completion_percentage": progress.completion_percentage,
        "quiz_scores": progress.quiz_scores,
        "weak_points": progress.weak_points,
        "strong_points": progress.strong_points,
        "updated_at": progress.updated_at.isoformat() if progress.updated_at else None,
    }


@router.get("/overview")
async def get_progress_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Progress).where(Progress.user_id == current_user.id)
    )
    records = result.scalars().all()

    total_learning_time = 0
    all_weak_points = set()
    all_strong_points = set()
    module_details = []

    for r in records:
        total_learning_time += r.learning_time_minutes or 0

        if r.weak_points:
            all_weak_points.update(r.weak_points)
        if r.strong_points:
            all_strong_points.update(r.strong_points)

        module_title = None
        path_title = None
        module_status = None
        module_progress = None
        if r.module_id:
            mod_result = await db.execute(
                select(Module).where(Module.id == r.module_id)
            )
            module = mod_result.scalar_one_or_none()
            if module:
                module_title = module.title
                module_status = module.status
                module_progress = module.progress

                path_result = await db.execute(
                    select(LearningPath).where(LearningPath.id == module.path_id)
                )
                path = path_result.scalar_one_or_none()
                if path:
                    path_title = path.title

        module_details.append(
            {
                "module_id": r.module_id,
                "module_title": module_title,
                "path_title": path_title,
                "module_status": module_status,
                "module_progress": module_progress,
                "learning_time_minutes": r.learning_time_minutes,
                "completion_percentage": r.completion_percentage,
                "quiz_scores": r.quiz_scores,
                "weak_points": r.weak_points,
                "strong_points": r.strong_points,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
        )

    total_completion = (
        sum(r.completion_percentage for r in records) / len(records)
        if records
        else 0.0
    )

    return {
        "user_id": current_user.id,
        "module_count": len(records),
        "total_learning_time_minutes": total_learning_time,
        "overall_completion": round(total_completion, 1),
        "weak_points": list(all_weak_points),
        "strong_points": list(all_strong_points),
        "module_details": module_details,
    }
