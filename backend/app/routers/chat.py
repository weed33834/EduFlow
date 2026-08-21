"""对话路由（SSE 流式）— Agent 核心入口"""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Session, Message, StudentProfile
from app.agents.graph import agent_graph

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None


@router.post("/chat")
async def chat(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE 流式对话

    前端用 EventSource 或 fetch + ReadableStream 接收。
    v0.1.0 先返回完整回复（非增量流式），v0.6.0 再做真正的流式输出。
    """
    # 获取或创建会话
    if req.session_id:
        result = await db.execute(
            select(Session).where(Session.id == req.session_id, Session.user_id == user.id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        session = Session(user_id=user.id)
        db.add(session)
        await db.flush()

    # 保存用户消息
    db.add(Message(
        session_id=session.id,
        role="user",
        content=req.message,
    ))
    await db.commit()

    # 获取对话历史（最近 6 条消息 = 3 轮对话）
    msg_result = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.created_at)
        .limit(20)
    )
    all_msgs = msg_result.scalars().all()
    history = [{"role": m.role, "content": m.content} for m in all_msgs[:-1]]  # 排除刚加的用户消息

    # 获取学生画像
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    profile_dict = {
        "current_level": profile.current_level if profile else "beginner",
        "learning_goal": profile.learning_goal or "" if profile else "",
    }

    # 执行 Agent 状态机
    initial_state = {
        "user_message": req.message,
        "user_id": user.id,
        "session_id": session.id,
        "history": history,
        "student_profile": profile_dict,
    }

    final_state = await agent_graph.ainvoke(initial_state)

    # 获取回复
    response_chunks = final_state.get("response_chunks", ["抱歉，我暂时无法回复。"])
    reply_text = "".join(response_chunks)

    # 如果是题目，也保存 quiz 数据到 metadata
    metadata = {
        "intent": final_state.get("intent"),
        "action": final_state.get("action_plan"),
    }
    if final_state.get("quiz_question"):
        metadata["quiz"] = final_state["quiz_question"]

    # 保存助手消息
    db.add(Message(
        session_id=session.id,
        role="assistant",
        content=reply_text,
        metadata_=metadata,
    ))
    session.ended_at = datetime.now()
    await db.commit()

    # SSE 返回
    async def event_stream():
        data = {
            "type": "quiz" if final_state.get("quiz_question") else "message",
            "content": reply_text,
            "session_id": session.id,
        }
        if final_state.get("quiz_question"):
            data["quiz"] = final_state["quiz_question"]
        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        yield "data: [done]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": str(session.id),
        },
    )
