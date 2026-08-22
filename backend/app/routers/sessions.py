"""会话管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Session, Message

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionSummary(BaseModel):
    id: int
    title: str | None = None
    started_at: str | None
    ended_at: str | None
    message_count: int
    last_message: str | None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    metadata: dict | None = None
    created_at: str | None


class SessionDetail(BaseModel):
    id: int
    started_at: str | None
    messages: list[MessageResponse]


@router.get("", response_model=list[SessionSummary])
async def list_sessions(
    archived: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出用户的会话（默认不含归档；archived=true 只看归档；置顶在前）"""
    result = await db.execute(
        select(Session)
        .where(Session.user_id == user.id, Session.archived == archived)
        .order_by(Session.pinned.desc(), desc(Session.created_at))
        .limit(50)
    )
    sessions = result.scalars().all()

    summaries = []
    for s in sessions:
        # 最后一条消息
        last_result = await db.execute(
            select(Message)
            .where(Message.session_id == s.id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )
        last_msg = last_result.scalar_one_or_none()

        count_result = await db.execute(
            select(func.count()).where(Message.session_id == s.id)
        )
        count = count_result.scalar() or 0

        summaries.append(SessionSummary(
            id=s.id,
            title=s.summary,
            started_at=s.started_at.isoformat() if s.started_at else None,
            ended_at=s.ended_at.isoformat() if s.ended_at else None,
            message_count=count,
            last_message=last_msg.content[:100] if last_msg else None,
        ))
    return summaries


class SessionUpdate(BaseModel):
    summary: str | None = None
    pinned: bool | None = None
    archived: bool | None = None


@router.patch("/{session_id}")
async def update_session(
    session_id: int,
    data: SessionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新会话元信息：重命名 / 置顶 / 归档"""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    if data.summary is not None:
        cleaned = " ".join(data.summary.split())[:60]
        session.summary = cleaned or None
    if data.pinned is not None:
        session.pinned = data.pinned
    if data.archived is not None:
        session.archived = data.archived
    await db.commit()
    return {
        "ok": True,
        "summary": session.summary,
        "pinned": session.pinned,
        "archived": session.archived,
    }


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取会话详情"""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    msg_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    return SessionDetail(
        id=session.id,
        started_at=session.started_at.isoformat() if session.started_at else None,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                metadata=m.metadata_ if m.metadata_ else None,
                created_at=m.created_at.isoformat() if m.created_at else None,
            )
            for m in messages
        ],
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除会话"""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    await db.delete(session)
    await db.commit()
    return {"ok": True}
