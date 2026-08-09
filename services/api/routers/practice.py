from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from models.learning import PracticeSession
from datetime import datetime

router = APIRouter(prefix="/api/practice", tags=["practice"])

class SubmitAnswer(BaseModel):
    session_id: int
    question_id: int
    answer: str
    is_correct: bool

@router.post("/sessions")
async def create_session(module_id: int, session_type: str = "quiz", db: AsyncSession = Depends(get_db)):
    session = PracticeSession(user_id=1, module_id=module_id, session_type=session_type)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.post("/submit")
async def submit_answer(req: SubmitAnswer, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PracticeSession).where(PracticeSession.id == req.session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    answers = session.answers or []
    answers.append({"question_id": req.question_id, "answer": req.answer, "is_correct": req.is_correct})
    session.answers = answers
    correct_count = sum(1 for a in answers if a["is_correct"])
    session.score = round(correct_count / len(answers) * 100, 1) if answers else 0
    await db.commit()
    return {"score": session.score, "total": len(answers), "correct": correct_count}