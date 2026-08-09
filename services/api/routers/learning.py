from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from models.learning import LearningPath, Module

router = APIRouter(prefix="/api/learning", tags=["learning"])

class PathCreate(BaseModel):
    title: str
    description: str = ""
    goal: str = ""
    difficulty: str = "beginner"

class ModuleCreate(BaseModel):
    path_id: int
    title: str
    description: str = ""
    order: int = 0
    content: list = []

@router.post("/paths")
async def create_path(req: PathCreate, db: AsyncSession = Depends(get_db)):
    path = LearningPath(title=req.title, description=req.description, goal=req.goal, difficulty=req.difficulty, user_id=1)
    db.add(path)
    await db.commit()
    await db.refresh(path)
    return path

@router.get("/paths")
async def list_paths(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LearningPath).order_by(LearningPath.created_at.desc()))
    return result.scalars().all()

@router.get("/paths/{path_id}")
async def get_path(path_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LearningPath).where(LearningPath.id == path_id))
    path = result.scalar_one_or_none()
    if not path:
        raise HTTPException(status_code=404, detail="Path not found")
    modules_result = await db.execute(select(Module).where(Module.path_id == path_id).order_by(Module.order))
    return {"path": path, "modules": modules_result.scalars().all()}

@router.post("/modules")
async def create_module(req: ModuleCreate, db: AsyncSession = Depends(get_db)):
    module = Module(path_id=req.path_id, title=req.title, description=req.description, order=req.order, content=req.content)
    db.add(module)
    await db.commit()
    await db.refresh(module)
    return module