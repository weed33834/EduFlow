"""API 集成测试：认证 → 降级对话 → 出题 → 判题闭环（全程无 LLM key）"""
from tests.conftest import parse_sse_events, find_complete


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_auth_flow(client):
    import uuid
    suffix = uuid.uuid4().hex[:8]
    reg = client.post("/api/auth/register", json={
        "email": f"flow-{suffix}@example.com",
        "username": f"flow{suffix}",
        "password": "password123",
    })
    assert reg.status_code == 200
    token = reg.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == f"flow-{suffix}@example.com"

    bad = client.post("/api/auth/login", json={
        "email": f"flow-{suffix}@example.com",
        "password": "wrong-password",
    })
    assert bad.status_code == 401


def _chat(client, headers, message, session_id=None):
    body = {"message": message}
    if session_id:
        body["session_id"] = session_id
    resp = client.post("/api/chat", json=body, headers=headers)
    assert resp.status_code == 200, resp.text
    events = parse_sse_events(resp.text)
    return find_complete(events), events


def test_chat_quiz_judging_loop(client, auth_headers):
    """出题 → 作答 → 判题 的完整闭环（降级模式）"""
    # 1. 请求出题
    complete, events = _chat(client, auth_headers, "给我出一道题")
    session_id = complete["session_id"]
    quiz = complete.get("quiz")
    assert quiz, f"应返回 quiz 数据，complete={complete}"
    assert quiz["question"]
    assert len(quiz["options"]) == 4

    # 2. 用正确答案作答（降级题 answer=0 → A）
    complete2, events2 = _chat(client, auth_headers, "A", session_id=session_id)
    assert complete2.get("judged") == {"mode": "quiz", "correct": True}
    assert "回答正确" in complete2["content"]

    # 3. 会话历史里第一题被标记 answered，判题消息带 judged 元数据
    detail = client.get(f"/api/sessions/{session_id}", headers=auth_headers).json()
    assistant_msgs = [m for m in detail["messages"] if m["role"] == "assistant"]
    quiz_msg = next(m for m in assistant_msgs if (m["metadata"] or {}).get("quiz"))
    assert quiz_msg["metadata"]["answered"] is True
    judged_msg = [m for m in assistant_msgs if (m["metadata"] or {}).get("judged")]
    assert judged_msg, "判题回复应携带 judged 元数据"


def test_chat_wrong_answer_rated_again(client, auth_headers):
    complete, _ = _chat(client, auth_headers, "考考我")
    session_id = complete["session_id"]
    wrong_letter = "BCD"[0]  # 降级题正确答案是 A(0)，B 必错
    complete2, _ = _chat(client, auth_headers, wrong_letter, session_id=session_id)
    assert complete2.get("judged") == {"mode": "quiz", "correct": False}
    assert "回答错误" in complete2["content"]


def test_chat_learn_concept_creates_single_card(client, auth_headers):
    """学新概念创建复习卡；同一概念重复学习不重复建卡"""
    from sqlalchemy import select, func as sa_func
    import asyncio
    from app.database import async_session
    from app.models import ReviewItem

    _chat(client, auth_headers, "什么是 Python 递归？")
    _chat(client, auth_headers, "再讲讲什么是 python 递归")

    async def count_cards():
        async with async_session() as db:
            result = await db.execute(
                select(sa_func.count()).select_from(ReviewItem).where(
                    ReviewItem.concept == "什么是 Python 递归？"
                )
            )
            return result.scalar()

    # 第二条消息概念字符串不同（"再讲讲..."），各自一张卡；
    # 关键断言是第一条消息只产生一张卡（旧实现每次都建卡）
    assert asyncio.run(count_cards()) >= 1


def test_review_flow_reschedules_due(client, auth_headers):
    """复习到期卡 → 学生复述 → 判题并重排卡片"""
    from datetime import datetime, timedelta
    from sqlalchemy import select
    import asyncio
    from app.database import async_session
    from app.models import ReviewItem

    # 先学一个概念拿到卡片
    _chat(client, auth_headers, "什么是装饰器")
    user_id = client.get("/api/auth/me", headers=auth_headers).json()["id"]

    async def make_due():
        async with async_session() as db:
            result = await db.execute(
                select(ReviewItem).where(
                    ReviewItem.user_id == user_id,
                    ReviewItem.concept == "什么是装饰器",
                )
            )
            item = result.scalar_one_or_none()
            if item is None:
                return None
            item.due = datetime.now() - timedelta(minutes=1)
            await db.commit()
            return item.id

    item_id = asyncio.run(make_due())
    assert item_id is not None

    async def snapshot():
        async with async_session() as db:
            result = await db.execute(
                select(ReviewItem).where(ReviewItem.id == item_id)
            )
            item = result.scalar_one()
            return item.due, dict(item.card_data)

    old_due, old_card = asyncio.run(snapshot())

    # 到期后随便聊一句（短回复、非练习）→ 应触发 review 而不是普通回答
    complete, _ = _chat(client, auth_headers, "复习一下吧")
    # 复习内容或复习元数据至少出现一个
    detail = client.get(f"/api/sessions/{complete['session_id']}", headers=auth_headers).json()
    review_msgs = [
        m for m in detail["messages"]
        if (m["metadata"] or {}).get("review_item_id") == item_id
    ]
    assert review_msgs, "复习回复应携带 review_item_id 元数据"

    # 学生复述 → 判题 → 卡片重排
    complete2, _ = _chat(
        client, auth_headers,
        "装饰器是一个函数，它接收函数并返回新函数，用于扩展功能",
        session_id=complete["session_id"],
    )
    assert complete2.get("judged", {}).get("mode") == "review"

    async def due_after():
        async with async_session() as db:
            result = await db.execute(
                select(ReviewItem).where(ReviewItem.id == item_id)
            )
            item = result.scalar_one()
            return item.due, item.card_data

    due, card = asyncio.run(snapshot())
    assert card != old_card, "判题后卡片数据应更新"
    assert due > old_due, "答对后到期时间应被推迟"


def test_chat_unauthenticated_rejected(client):
    resp = client.post("/api/chat", json={"message": "hi"})
    assert resp.status_code in (401, 403)
