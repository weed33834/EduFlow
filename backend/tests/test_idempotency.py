"""幂等键测试：同 request_id 重复请求不重复入库，回放上次回复"""
from tests.conftest import find_complete, parse_sse_events


def test_duplicate_request_id_replays_without_new_rows(client, auth_headers):
    from sqlalchemy import select, func as sa_func
    import asyncio
    from app.database import async_session
    from app.models import Message

    # 第一次请求
    resp1 = client.post("/api/chat", json={
        "message": "给我出一道题",
        "request_id": "req-idempotent-1",
    }, headers=auth_headers)
    assert resp1.status_code == 200
    complete1 = find_complete(parse_sse_events(resp1.text))
    session_id = complete1["session_id"]
    assert complete1.get("duplicate") is None

    # 同键重复请求 → 回放，不新增任何消息行
    resp2 = client.post("/api/chat", json={
        "message": "给我出一道题",
        "session_id": session_id,
        "request_id": "req-idempotent-1",
    }, headers=auth_headers)
    assert resp2.status_code == 200
    events2 = parse_sse_events(resp2.text)
    complete2 = find_complete(events2)
    assert complete2.get("duplicate") is True
    assert complete2["content"] == complete1["content"]
    assert not any(e.get("type") == "stream" for e in events2), "回放不应有增量流"

    async def count_msgs():
        async with async_session() as db:
            result = await db.execute(
                select(sa_func.count()).select_from(Message).where(
                    Message.session_id == session_id
                )
            )
            return result.scalar()

    total = asyncio.run(count_msgs())
    assert total == 2, f"应只有 user+assistant 各一条，实际 {total}"


def test_different_request_ids_are_not_deduped(client, auth_headers):
    resp1 = client.post("/api/chat", json={
        "message": "你好",
        "request_id": "req-a",
    }, headers=auth_headers)
    s1 = find_complete(parse_sse_events(resp1.text))["session_id"]

    resp2 = client.post("/api/chat", json={
        "message": "再打个招呼",
        "session_id": s1,
        "request_id": "req-b",
    }, headers=auth_headers)
    complete2 = find_complete(parse_sse_events(resp2.text))
    assert complete2.get("duplicate") is None


def test_request_without_id_never_dedupes(client, auth_headers):
    resp1 = client.post("/api/chat", json={"message": "什么是递归"}, headers=auth_headers)
    s1 = find_complete(parse_sse_events(resp1.text))["session_id"]

    resp2 = client.post("/api/chat", json={
        "message": "什么是递归", "session_id": s1,
    }, headers=auth_headers)
    complete2 = find_complete(parse_sse_events(resp2.text))
    assert complete2.get("duplicate") is None
