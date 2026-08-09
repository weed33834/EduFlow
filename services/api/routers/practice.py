from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from core.database import get_db
from core.config import settings
from core.deps import get_current_user
from models.user import User
from models.learning import PracticeSession, Module, LearningPath, Progress
from routers.learning import _recalculate_path_progress

router = APIRouter(prefix="/api/practice", tags=["practice"])


class SessionCreate(BaseModel):
    module_id: int | None = None
    session_type: str = "quiz"
    topic: str | None = None
    questions: list = []


class SubmitAnswer(BaseModel):
    session_id: int
    question_id: int
    answer: str
    is_correct: bool


class CompleteRequest(BaseModel):
    weak_points: list[str] = []
    strong_points: list[str] = []


def _session_dict(session: PracticeSession) -> dict:
    return {
        "id": session.id,
        "user_id": session.user_id,
        "module_id": session.module_id,
        "session_type": session.session_type,
        "topic": session.topic,
        "questions": session.questions,
        "answers": session.answers,
        "score": session.score,
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
    }


async def _verify_session_ownership(
    db: AsyncSession, session: PracticeSession, current_user: User
) -> None:
    """Verify that the session belongs to the current user."""
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your practice session",
        )


@router.post("/sessions")
async def create_session(
    req: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # If module_id provided, verify it belongs to the user
    if req.module_id is not None:
        module_result = await db.execute(
            select(Module).where(Module.id == req.module_id)
        )
        module = module_result.scalar_one_or_none()
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

    session = PracticeSession(
        user_id=current_user.id,
        module_id=req.module_id,
        session_type=req.session_type,
        topic=req.topic,
        questions=req.questions,
        answers=[],
        score=0.0,
        status="in_progress",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _session_dict(session)


@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PracticeSession)
        .where(PracticeSession.user_id == current_user.id)
        .order_by(PracticeSession.started_at.desc())
    )
    sessions = result.scalars().all()
    return [_session_dict(s) for s in sessions]


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PracticeSession).where(PracticeSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    await _verify_session_ownership(db, session, current_user)
    return _session_dict(session)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PracticeSession).where(PracticeSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    await _verify_session_ownership(db, session, current_user)

    await db.delete(session)
    await db.commit()
    return {"detail": "Session deleted"}


@router.post("/submit")
async def submit_answer(
    req: SubmitAnswer,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PracticeSession).where(PracticeSession.id == req.session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    await _verify_session_ownership(db, session, current_user)

    answers = session.answers or []
    answers.append(
        {
            "question_id": req.question_id,
            "answer": req.answer,
            "is_correct": req.is_correct,
        }
    )
    session.answers = answers
    correct_count = sum(1 for a in answers if a["is_correct"])
    session.score = round(correct_count / len(answers) * 100, 1) if answers else 0.0

    await db.commit()
    await db.refresh(session)
    return {
        "score": session.score,
        "total": len(answers),
        "correct": correct_count,
    }


@router.put("/sessions/{session_id}/complete")
async def complete_session(
    session_id: int,
    req: CompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PracticeSession).where(PracticeSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    await _verify_session_ownership(db, session, current_user)

    # Calculate final score from answers if not already set
    answers = session.answers or []
    if answers:
        correct_count = sum(1 for a in answers if a["is_correct"])
        session.score = round(correct_count / len(answers) * 100, 1)
    elif session.score is None:
        session.score = 0.0

    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)

    passed = session.score >= settings.PASS_SCORE_THRESHOLD

    # Update module status and progress if linked to a module
    module_id = session.module_id
    if module_id is not None:
        module_result = await db.execute(
            select(Module).where(Module.id == module_id)
        )
        module = module_result.scalar_one_or_none()
        if module:
            if passed:
                module.status = "completed"
                module.progress = 100.0
            else:
                module.status = "in_progress"
                if module.progress is None or module.progress < 50.0:
                    module.progress = 50.0

            await db.flush()

            # Create or update Progress record
            progress_result = await db.execute(
                select(Progress).where(
                    Progress.user_id == current_user.id,
                    Progress.module_id == module_id,
                )
            )
            progress = progress_result.scalar_one_or_none()

            quiz_scores = []
            if progress and progress.quiz_scores:
                quiz_scores = list(progress.quiz_scores)
            quiz_scores.append(
                {
                    "session_id": session.id,
                    "score": session.score,
                    "passed": passed,
                    "completed_at": session.completed_at.isoformat(),
                }
            )

            # Calculate completion percentage based on pass status
            completion = 100.0 if passed else (module.progress or 50.0)

            # Merge weak/strong points
            weak = set(progress.weak_points) if progress and progress.weak_points else set()
            weak.update(req.weak_points)
            strong = set(progress.strong_points) if progress and progress.strong_points else set()
            strong.update(req.strong_points)

            if progress:
                progress.quiz_scores = quiz_scores
                progress.completion_percentage = completion
                progress.weak_points = list(weak)
                progress.strong_points = list(strong)
            else:
                progress = Progress(
                    user_id=current_user.id,
                    module_id=module_id,
                    learning_time_minutes=0,
                    completion_percentage=completion,
                    quiz_scores=quiz_scores,
                    weak_points=list(weak),
                    strong_points=list(strong),
                )
                db.add(progress)

            await db.flush()

            # Recalculate path progress
            await _recalculate_path_progress(db, module.path_id)

    await db.commit()
    await db.refresh(session)

    return {
        "session": _session_dict(session),
        "passed": passed,
        "pass_threshold": settings.PASS_SCORE_THRESHOLD,
        "score": session.score,
    }
