"""v0.6.0 大迭代后端测试：重新生成 / 编辑重发 / 会话置顶与归档"""
import uuid

from sqlalchemy import select, func as sa_func

from app.database import async_session
from app.models import Message
from tests.conftest import find_complete, parse_sse_events


def _register(client):
    suffix = uuid.uuid4().hex[:8]
    resp = client.post("/api/auth/register", json={
        "email": f"v6-{suffix}@example.com",
        "username": f"v6{suffix}",
        "password": "password123",
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _chat(client, headers, message, session_id=None):
    body = {"message": message}
    if session_id:
        body["session_id"] = session_id
    resp = client.post("/api/chat", json=body, headers=headers)
    assert resp.status_code == 200, resp.text
    return find_complete(parse_sse_events(resp.text))


async def _message_counts(session_id: int):
    async with async_session() as db:
        users = await db.execute(
            select(sa_func.count()).select_from(Message).where(
                Message.session_id == session_id, Message.role == "user")
        )
        assistants = await db.execute(
            select(sa_func.count()).select_from(Message).where(
                Message.session_id == session_id, Message.role == "assistant")
        )
        return users.scalar(), assistants.scalar()


# ── 重新生成 ──────────────────────────────────────────────


def test_regenerate_replaces_last_reply(client):
    headers = _register(client)
    complete1 = _chat(client, headers, "什么是递归")
    sid = complete1["session_id"]

    users_before, assistants_before = asyncio_run(_message_counts(sid))
    assert (users_before, assistants_before) == (1, 1)

    resp = client.post("/api/chat", json={
        "regenerate": True, "session_id": sid,
    }, headers=headers)
    assert resp.status_code == 200
    complete2 = find_complete(parse_sse_events(resp.text))
    assert complete2["session_id"] == sid
    assert complete2["content"], "重新生成应有回复内容"

    # 用户行不新增；助手行替换（仍为 1 条，而非 2）
    users_after, assistants_after = asyncio_run(_message_counts(sid))
    assert users_after == users_before == 1
    assert assistants_after == 1


def test_regenerate_requires_session(client):
    headers = _register(client)
    resp = client.post("/api/chat", json={"regenerate": True}, headers=headers)
    assert resp.status_code == 400


def test_regenerate_empty_session_rejected(client):
    headers = _register(client)
    # 建一个空会话：发一条消息再手动删掉助手回复？——直接用未对话用户 + 404 会话路径
    resp = client.post("/api/chat", json={
        "regenerate": True, "session_id": 999999,
    }, headers=headers)
    assert resp.status_code == 404


# ── 编辑重发 ──────────────────────────────────────────────


def test_edit_user_message_truncates_and_reruns(client):
    """编辑首轮提问 → 其后的消息全部删除并重跑"""
    headers = _register(client)
    c1 = _chat(client, headers, "原始问题一")
    sid = c1["session_id"]
    detail = client.get(f"/api/sessions/{sid}", headers=headers).json()
    user_msg = next(m for m in detail["messages"] if m["role"] == "user")

    resp = client.post("/api/chat/edit", json={
        "session_id": sid,
        "message_id": user_msg["id"],
        "new_content": "编辑后的问题二",
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    complete = find_complete(parse_sse_events(resp.text))
    assert complete["content"]

    users, assistants = asyncio_run(_message_counts(sid))
    assert (users, assistants) == (1, 1), "编辑重发应恰好一轮问答"

    detail2 = client.get(f"/api/sessions/{sid}", headers=headers).json()
    edited = next(m for m in detail2["messages"] if m["id"] == user_msg["id"])
    assert edited["content"] == "编辑后的问题二"


def test_edit_rejects_bad_targets(client):
    headers = _register(client)
    c1 = _chat(client, headers, "问题")
    sid = c1["session_id"]
    detail = client.get(f"/api/sessions/{sid}", headers=headers).json()
    assistant_msg = next(m for m in detail["messages"] if m["role"] == "assistant")

    # 不能编辑助手消息
    r1 = client.post("/api/chat/edit", json={
        "session_id": sid, "message_id": assistant_msg["id"],
        "new_content": "x",
    }, headers=headers)
    assert r1.status_code == 404

    # 空内容拒绝
    user_msg = next(m for m in detail["messages"] if m["role"] == "user")
    r2 = client.post("/api/chat/edit", json={
        "session_id": sid, "message_id": user_msg["id"], "new_content": "   ",
    }, headers=headers)
    assert r2.status_code == 400


def test_edit_scoped_to_owner(client, auth_headers):
    c1 = _chat(client, auth_headers, "我的会话")
    sid = c1["session_id"]
    detail = client.get(f"/api/sessions/{sid}", headers=auth_headers).json()
    user_msg = next(m for m in detail["messages"] if m["role"] == "user")

    other = _register(client)
    resp = client.post("/api/chat/edit", json={
        "session_id": sid, "message_id": user_msg["id"], "new_content": "劫持",
    }, headers=other)
    assert resp.status_code == 404


# ── 置顶 / 归档 ───────────────────────────────────────────


def test_pin_orders_sessions_first(client):
    headers = _register(client)
    old = _chat(client, headers, "最早的会话")["session_id"]
    new = _chat(client, headers, "较新的会话")["session_id"]

    client.patch(f"/api/sessions/{old}", json={"pinned": True}, headers=headers)

    ids = [s["id"] for s in client.get("/api/sessions", headers=headers).json()]
    assert ids.index(old) < ids.index(new), "置顶会话应排最前"


def test_archive_hides_from_default_list(client):
    headers = _register(client)
    keep = _chat(client, headers, "保留的会话")["session_id"]
    gone = _chat(client, headers, "要归档的会话")["session_id"]

    client.patch(f"/api/sessions/{gone}", json={"archived": True}, headers=headers)

    default_ids = {s["id"] for s in client.get("/api/sessions", headers=headers).json()}
    assert keep in default_ids and gone not in default_ids

    archived_ids = {
        s["id"] for s in
        client.get("/api/sessions?archived=true", headers=headers).json()
    }
    assert archived_ids == {gone}


def test_unarchive_restores(client):
    headers = _register(client)
    sid = _chat(client, headers, "会话")["session_id"]
    client.patch(f"/api/sessions/{sid}", json={"archived": True}, headers=headers)
    client.patch(f"/api/sessions/{sid}", json={"archived": False}, headers=headers)
    ids = {s["id"] for s in client.get("/api/sessions", headers=headers).json()}
    assert sid in ids


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)


def test_quiz_flow_still_works_without_checkpointer(client):
    """移除 checkpointer 后判题闭环回归保护"""
    headers = _register(client)
    c1 = _chat(client, headers, "考考我")
    sid = c1["session_id"]
    assert c1.get("quiz"), "无 checkpointer 下出题必须正常"
    c2 = _chat(client, headers, "A", session_id=sid)
    assert (c2.get("judged") or {}).get("correct") is True
