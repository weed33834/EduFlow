"""
AI 会话持久化路由

提供会话的创建、列表、详情、删除，以及向会话追加消息的能力。
配合 AI 聊天接口使用：前端发送前把用户消息写入会话，收到回复后把助手消息写入，
实现跨设备/断线恢复的服务端会话记忆。
"""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.user import User
from models.conversation import Conversation, ConversationMessage

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

SUPPORTED_AGENTS = ("tutor", "buddy")


class ConversationCreate(BaseModel):
    agent_type: str = "tutor"
    title: str = ""


class MessageAppend(BaseModel):
    role: str  # user / assistant
    content: str


def _conv_dict(c: Conversation, message_count: int = 0, last_message: str = "") -> dict:
    return {
        "id": c.id,
        "agent_type": c.agent_type,
        "title": c.title,
        "message_count": message_count,
        "last_message": last_message,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _msg_dict(m: ConversationMessage) -> dict:
    return {
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


async def _get_owned(db: AsyncSession, conv_id: int, user_id: int) -> Conversation:
    result = await db.execute(
        select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return conv


@router.get("/")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出当前用户的会话(含最近消息预览)。"""
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == current_user.id).order_by(Conversation.updated_at.desc())
    )
    convs = result.scalars().all()
    out = []
    for c in convs:
        # 最近一条消息作为预览
        last = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == c.id)
            .order_by(ConversationMessage.id.desc())
            .limit(1)
        )
        last_msg = last.scalar_one_or_none()
        count_res = await db.execute(
            select(func.count()).select_from(ConversationMessage).where(ConversationMessage.conversation_id == c.id)
        )
        count = count_res.scalar() or 0
        out.append(_conv_dict(c, count, last_msg.content if last_msg else ""))
    return {"conversations": out}


@router.post("/")
async def create_conversation(
    req: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.agent_type not in SUPPORTED_AGENTS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不支持的智能体类型")
    conv = Conversation(
        user_id=current_user.id,
        agent_type=req.agent_type,
        title=req.title or "新对话",
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return _conv_dict(conv)


@router.get("/{conv_id}")
async def get_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await _get_owned(db, conv_id, current_user.id)
    msgs = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conv_id)
        .order_by(ConversationMessage.id)
    )
    messages = [_msg_dict(m) for m in msgs.scalars().all()]
    return {
        **_conv_dict(conv, message_count=len(messages)),
        "messages": messages,
    }


@router.delete("/{conv_id}")
async def delete_conversation(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await _get_owned(db, conv_id, current_user.id)
    await db.delete(conv)
    await db.commit()
    return {"detail": "会话已删除"}


@router.post("/{conv_id}/messages")
async def append_message(
    conv_id: int,
    req: MessageAppend,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await _get_owned(db, conv_id, current_user.id)
    if req.role not in ("user", "assistant"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="role 须为 user 或 assistant")
    if not req.content or not req.content.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="消息内容不能为空")

    msg = ConversationMessage(conversation_id=conv.id, role=req.role, content=req.content)
    db.add(msg)
    # 首次助手消息后自动生成标题
    if conv.title in ("", "新对话") and req.role == "user":
        conv.title = req.content.strip()[:40]
    conv.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(msg)
    return _msg_dict(msg)
