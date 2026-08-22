"""会话命名测试：自动命名 + 重命名（ChatGPT 式）"""
from tests.conftest import find_complete, parse_sse_events


def _register(client):
    import uuid
    suffix = uuid.uuid4().hex[:8]
    resp = client.post("/api/auth/register", json={
        "email": f"name-{suffix}@example.com",
        "username": f"name{suffix}",
        "password": "password123",
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_first_message_auto_titles_session(client):
    headers = _register(client)
    resp = client.post("/api/chat", json={"message": "帮我理解 Python 装饰器的原理"},
                       headers=headers)
    sid = find_complete(parse_sse_events(resp.text))["session_id"]

    sessions = client.get("/api/sessions", headers=headers).json()
    target = next(s for s in sessions if s["id"] == sid)
    assert target["title"] == "帮我理解 Python 装饰器的原理"


def test_title_survives_subsequent_messages(client):
    """后续消息不覆盖已有标题"""
    headers = _register(client)
    resp1 = client.post("/api/chat", json={"message": "第一轮的主题是闭包"}, headers=headers)
    sid = find_complete(parse_sse_events(resp1.text))["session_id"]
    client.post("/api/chat", json={
        "message": "第二轮完全不同的内容", "session_id": sid,
    }, headers=headers)

    target = next(s for s in client.get("/api/sessions", headers=headers).json()
                  if s["id"] == sid)
    assert target["title"] == "第一轮的主题是闭包"


def test_rename_session(client):
    headers = _register(client)
    resp = client.post("/api/chat", json={"message": "随便聊聊"}, headers=headers)
    sid = find_complete(parse_sse_events(resp.text))["session_id"]

    renamed = client.patch(f"/api/sessions/{sid}", json={"summary": "  Q3 复习计划  "},
                           headers=headers)
    assert renamed.status_code == 200
    assert renamed.json()["summary"] == "Q3 复习计划"

    target = next(s for s in client.get("/api/sessions", headers=headers).json()
                  if s["id"] == sid)
    assert target["title"] == "Q3 复习计划"


def test_rename_scoped_to_owner(client, auth_headers):
    """别人的会话不可重命名"""
    resp = client.post("/api/chat", json={"message": "我的会话"}, headers=auth_headers)
    sid = find_complete(parse_sse_events(resp.text))["session_id"]

    other_headers = _register(client)
    resp2 = client.patch(f"/api/sessions/{sid}", json={"summary": "劫持"},
                         headers=other_headers)
    assert resp2.status_code == 404
