"""对话路由（SSE 流式）— Agent 核心入口

集成开源组件：
- LangGraph Checkpointer：自动管理对话历史（无需手动查数据库）
- fsrs 包：间隔重复，学生学过概念后自动创建复习卡片
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Session, Message, StudentProfile, ReviewItem
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

    对话历史由 LangGraph MemorySaver 自动管理（按 session_id 持久化），
    不再手动查数据库拼 history。
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

    # 保存用户消息（给前端展示用，Agent 历史由 checkpointer 管）
    db.add(Message(
        session_id=session.id,
        role="user",
        content=req.message,
    ))
    await db.commit()

    # 获取学生画像
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    profile_dict = {
        "current_level": profile.current_level if profile else "beginner",
        "learning_goal": profile.learning_goal or "" if profile else "",
    }

    # 查询到期的 FSRS 复习项
    now = datetime.now()
    review_result = await db.execute(
        select(ReviewItem)
        .where(ReviewItem.user_id == user.id, ReviewItem.due <= now)
        .order_by(ReviewItem.due)
        .limit(3)
    )
    review_items = [
        {"concept": r.concept, "card_data": r.card_data, "id": r.id}
        for r in review_result.scalars().all()
    ]

    # 执行 Agent 状态机
    # checkpointer 通过 thread_id 自动恢复之前的对话历史
    initial_state = {
        "user_message": req.message,
        "user_id": user.id,
        "session_id": session.id,
        "student_profile": profile_dict,
        "review_items": review_items,
    }

    final_state = await agent_graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": str(session.id)}},
    )

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

    # 如果学生学了新概念，用 fsrs 包创建间隔重复卡片
    if final_state.get("intent") == "learn_concept" and final_state.get("teach_content"):
        try:
            from fsrs import Card, Scheduler

            scheduler = Scheduler()
            card = Card()
            # 初始评分 3（Good）— 学生刚学完，假设记得
            card, _ = scheduler.review_card(card, rating=3)

            due = card.due
            # 确保 due 是 naive datetime（SQLite 不支持 tz-aware）
            if hasattr(due, 'tzinfo') and due.tzinfo:
                due = due.replace(tzinfo=None)

            db.add(ReviewItem(
                user_id=user.id,
                concept=req.message[:200],
                card_data=card.to_dict(),
                due=due,
            ))
            await db.commit()
        except Exception:
            # FSRS 失败不影响主流程
            pass

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
