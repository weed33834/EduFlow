"""profile 路由直测（审计缺口：GET/PUT 此前无用例覆盖）"""
import uuid


def _register(client):
    suffix = uuid.uuid4().hex[:8]
    resp = client.post("/api/auth/register", json={
        "email": f"prof-api-{suffix}@example.com",
        "username": f"profapi{suffix}",
        "password": "password123",
    })
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_get_profile_creates_default(client):
    """首次 GET 自动创建默认画像"""
    headers = _register(client)
    resp = client.get("/api/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_level"] == "beginner"
    assert data["learning_goal"] is None
    assert data["strengths"] == []
    assert data["weaknesses"] == []
    assert data["total_study_minutes"] == 0


def test_get_profile_is_stable_on_repeat(client):
    """二次 GET 不重复创建，返回一致"""
    headers = _register(client)
    first = client.get("/api/profile", headers=headers).json()
    second = client.get("/api/profile", headers=headers).json()
    assert first == second


def test_update_profile_fields(client):
    headers = _register(client)
    resp = client.put("/api/profile", json={
        "learning_goal": "三个月内独立完成爬虫项目",
        "current_level": "intermediate",
        "preferred_style": "practice-first",
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["learning_goal"] == "三个月内独立完成爬虫项目"
    assert data["current_level"] == "intermediate"
    assert data["preferred_style"] == "practice-first"


def test_update_partial_keeps_other_fields(client):
    """部分更新只改传入字段"""
    headers = _register(client)
    client.put("/api/profile", json={
        "learning_goal": "目标A", "current_level": "advanced",
    }, headers=headers)

    resp = client.put("/api/profile", json={"preferred_style": "reading"},
                      headers=headers)
    data = resp.json()
    assert data["preferred_style"] == "reading"
    assert data["learning_goal"] == "目标A", "未传字段不应被清空"
    assert data["current_level"] == "advanced"


def test_profile_requires_auth(client):
    assert client.get("/api/profile").status_code in (401, 403)
    assert client.put("/api/profile", json={"learning_goal": "x"}).status_code in (401, 403)
