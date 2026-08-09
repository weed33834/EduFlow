from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from core.database import get_db
from core.deps import get_current_user
from models.user import User
from models.learning import LearningPath, Module, PracticeSession, Progress

router = APIRouter(prefix="/api/learning", tags=["learning"])


class PathCreate(BaseModel):
    title: str
    description: str = ""
    goal: str = ""
    estimated_duration: int | None = None
    difficulty: str = "beginner"


class PathUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    goal: str | None = None
    estimated_duration: int | None = None
    difficulty: str | None = None
    status: str | None = None


class ModuleCreate(BaseModel):
    path_id: int
    title: str
    description: str = ""
    order: int = 0
    content: list = []
    estimated_minutes: int | None = None


class ModuleUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    order: int | None = None
    content: list | None = None
    status: str | None = None
    estimated_minutes: int | None = None


def _module_dict(module: Module) -> dict:
    return {
        "id": module.id,
        "path_id": module.path_id,
        "title": module.title,
        "description": module.description,
        "order": module.order,
        "content": module.content,
        "status": module.status,
        "progress": module.progress,
        "estimated_minutes": module.estimated_minutes,
        "created_at": module.created_at.isoformat() if module.created_at else None,
    }


def _path_dict(path: LearningPath) -> dict:
    return {
        "id": path.id,
        "user_id": path.user_id,
        "title": path.title,
        "description": path.description,
        "goal": path.goal,
        "estimated_duration": path.estimated_duration,
        "difficulty": path.difficulty,
        "status": path.status,
        "progress": path.progress,
        "created_at": path.created_at.isoformat() if path.created_at else None,
        "updated_at": path.updated_at.isoformat() if path.updated_at else None,
    }


async def _recalculate_path_progress(db: AsyncSession, path_id: int) -> LearningPath | None:
    """Recalculate the path progress based on its modules.
    Progress = completed_count / total * 100.
    Status: 'completed' if all modules completed, 'in_progress' if any module
    is in_progress or completed, otherwise 'not_started'.
    """
    result = await db.execute(
        select(Module).where(Module.path_id == path_id).order_by(Module.order)
    )
    modules = result.scalars().all()

    path_result = await db.execute(
        select(LearningPath).where(LearningPath.id == path_id)
    )
    path = path_result.scalar_one_or_none()
    if path is None:
        return None

    total = len(modules)
    if total == 0:
        path.progress = 0.0
        path.status = "not_started"
    else:
        completed_count = sum(1 for m in modules if m.status == "completed")
        path.progress = round(completed_count / total * 100, 1)

        has_in_progress = any(m.status == "in_progress" for m in modules)
        if completed_count == total:
            path.status = "completed"
        elif has_in_progress or completed_count > 0:
            path.status = "in_progress"
        else:
            path.status = "not_started"

    await db.flush()
    return path


# ---------------- Path endpoints ----------------

@router.post("/paths")
async def create_path(
    req: PathCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not req.title or not req.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Title cannot be empty",
        )

    path = LearningPath(
        title=req.title.strip(),
        description=req.description,
        goal=req.goal,
        estimated_duration=req.estimated_duration,
        difficulty=req.difficulty,
        user_id=current_user.id,
    )
    db.add(path)
    await db.commit()
    await db.refresh(path)
    return _path_dict(path)


@router.get("/paths")
async def list_paths(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LearningPath)
        .where(LearningPath.user_id == current_user.id)
        .order_by(LearningPath.created_at.desc())
    )
    paths = result.scalars().all()
    return [_path_dict(p) for p in paths]


@router.get("/paths/{path_id}")
async def get_path(
    path_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LearningPath).where(LearningPath.id == path_id)
    )
    path = result.scalar_one_or_none()
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path not found")
    if path.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your path")

    modules_result = await db.execute(
        select(Module).where(Module.path_id == path_id).order_by(Module.order)
    )
    modules = modules_result.scalars().all()
    return {
        "path": _path_dict(path),
        "modules": [_module_dict(m) for m in modules],
    }


@router.put("/paths/{path_id}")
async def update_path(
    path_id: int,
    req: PathUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LearningPath).where(LearningPath.id == path_id)
    )
    path = result.scalar_one_or_none()
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path not found")
    if path.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your path")

    if req.title is not None:
        if not req.title or not req.title.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Title cannot be empty",
            )
        path.title = req.title.strip()
    if req.description is not None:
        path.description = req.description
    if req.goal is not None:
        path.goal = req.goal
    if req.estimated_duration is not None:
        path.estimated_duration = req.estimated_duration
    if req.difficulty is not None:
        path.difficulty = req.difficulty
    if req.status is not None:
        path.status = req.status

    await db.commit()
    await db.refresh(path)
    return _path_dict(path)


@router.delete("/paths/{path_id}")
async def delete_path(
    path_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LearningPath).where(LearningPath.id == path_id)
    )
    path = result.scalar_one_or_none()
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path not found")
    if path.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your path")

    # Get module ids for cascade delete of practice sessions and progress
    modules_result = await db.execute(
        select(Module.id).where(Module.path_id == path_id)
    )
    module_ids = [row[0] for row in modules_result.all()]

    if module_ids:
        # Delete progress records linked to these modules
        await db.execute(
            delete(Progress).where(Progress.module_id.in_(module_ids))
        )
        # Delete practice sessions linked to these modules
        await db.execute(
            delete(PracticeSession).where(PracticeSession.module_id.in_(module_ids))
        )
        # Delete modules
        await db.execute(
            delete(Module).where(Module.path_id == path_id)
        )

    await db.delete(path)
    await db.commit()
    return {"detail": "Path deleted"}


# ---------------- Module endpoints ----------------

@router.post("/modules")
async def create_module(
    req: ModuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not req.title or not req.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Title cannot be empty",
        )

    # Verify path ownership
    path_result = await db.execute(
        select(LearningPath).where(LearningPath.id == req.path_id)
    )
    path = path_result.scalar_one_or_none()
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path not found")
    if path.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your path")

    module = Module(
        path_id=req.path_id,
        title=req.title.strip(),
        description=req.description,
        order=req.order,
        content=req.content,
        estimated_minutes=req.estimated_minutes,
    )
    db.add(module)
    await db.flush()

    # Recalculate path progress
    await _recalculate_path_progress(db, req.path_id)

    await db.commit()
    await db.refresh(module)
    return _module_dict(module)


@router.get("/modules/{module_id}")
async def get_module(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    # Verify ownership via path
    path_result = await db.execute(
        select(LearningPath).where(LearningPath.id == module.path_id)
    )
    path = path_result.scalar_one_or_none()
    if not path or path.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your module")

    return _module_dict(module)


@router.put("/modules/{module_id}")
async def update_module(
    module_id: int,
    req: ModuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    # Verify ownership via path
    path_result = await db.execute(
        select(LearningPath).where(LearningPath.id == module.path_id)
    )
    path = path_result.scalar_one_or_none()
    if not path or path.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your module")

    if req.title is not None:
        if not req.title or not req.title.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Title cannot be empty",
            )
        module.title = req.title.strip()
    if req.description is not None:
        module.description = req.description
    if req.order is not None:
        module.order = req.order
    if req.content is not None:
        module.content = req.content
    if req.status is not None:
        module.status = req.status
        # Update module progress based on status
        if req.status == "completed":
            module.progress = 100.0
        elif req.status == "in_progress":
            if module.progress is None or module.progress == 0.0 or module.progress == 100.0:
                module.progress = 50.0
        elif req.status == "not_started":
            module.progress = 0.0
    if req.estimated_minutes is not None:
        module.estimated_minutes = req.estimated_minutes

    await db.flush()

    # Recalculate path progress after status change
    if req.status is not None:
        await _recalculate_path_progress(db, module.path_id)

    await db.commit()
    await db.refresh(module)
    return _module_dict(module)


@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    # Verify ownership via path
    path_result = await db.execute(
        select(LearningPath).where(LearningPath.id == module.path_id)
    )
    path = path_result.scalar_one_or_none()
    if not path or path.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your module")

    path_id = module.path_id

    # Cascade delete practice sessions and progress linked to this module
    await db.execute(
        delete(PracticeSession).where(PracticeSession.module_id == module_id)
    )
    await db.execute(
        delete(Progress).where(Progress.module_id == module_id)
    )

    await db.delete(module)
    await db.flush()

    # Recalculate path progress after deletion
    await _recalculate_path_progress(db, path_id)

    await db.commit()
    return {"detail": "Module deleted"}
