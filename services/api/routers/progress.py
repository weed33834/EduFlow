from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from models.learning import Progress

router = APIRouter(prefix="/api/progress", tags=["progress"])

@router.get("/{user_id}")
async def get_progress(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Progress).where(Progress.user_id == user_id))
    records = result.scalars().all()
    total_completion = sum(r.completion_percentage for r in records) / max(len(records), 1)
    weak_points = set()
    for r in records:
        if r.weak_points:
            weak_points.update(r.weak_points)
    return {
        "overall_completion": round(total_completion, 1),
        "module_count": len(records),
        "weak_points": list(weak_points)[:10],
        "details": [
            {"module_id": r.module_id, "completion": r.completion_percentage, "learning_time": r.learning_time_minutes}
            for r in records
        ]
    }