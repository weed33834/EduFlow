"""EduFlow API 端到端冒烟测试。

覆盖：注册/登录、学习路径/模块、练习会话与判题、进度、Engine 网关(降级)。
运行前需安装测试依赖：
    pip install pytest httpx
"""
import os
import tempfile

# 必须在导入应用前设置环境，确保数据库引擎指向临时 SQLite
_DB = tempfile.mktemp(suffix="_eduflow_test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB}"
os.environ["ENV"] = "development"

from fastapi.testclient import TestClient  # noqa: E402
import pytest  # noqa: E402

from main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    """每个测试前重置临时数据库与内存限流计数，保证用例相互独立。"""
    if os.path.exists(_DB):
        os.remove(_DB)
    import routers.auth as auth_mod

    auth_mod._attempts.clear()
    yield


def _client():
    return TestClient(app)


def _auth(client: TestClient) -> str:
    r = client.post(
        "/api/auth/register",
        json={"email": "t@t.com", "username": "tester", "password": "pass1234"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_health():
    with _client() as c:
        r = c.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_register_login_and_weak_password_rejected():
    with _client() as c:
        # 弱密码被拒绝
        r = c.post(
            "/api/auth/register",
            json={"email": "a@b.com", "username": "userok", "password": "weak"},
        )
        assert r.status_code == 422

        token = _auth(c)
        # 登录（邮箱大小写不敏感）
        r = c.post(
            "/api/auth/login",
            json={"email": "T@T.COM", "password": "pass1234"},
        )
        assert r.status_code == 200
        headers = {"Authorization": f"Bearer {token}"}
        me = c.get("/api/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["username"] == "tester"


def test_full_learning_and_practice_flow():
    with _client() as c:
        token = _auth(c)
        headers = {"Authorization": f"Bearer {token}"}

        path = c.post(
            "/api/learning/paths",
            headers=headers,
            json={"title": "Python 入门", "goal": "学会 Python"},
        ).json()
        module = c.post(
            "/api/learning/modules",
            headers=headers,
            json={"path_id": path["id"], "title": "基础语法"},
        ).json()
        sess = c.post(
            "/api/practice/sessions",
            headers=headers,
            json={
                "module_id": module["id"],
                "questions": [
                    {"id": 1, "question": "q", "options": ["a", "b"], "answer": "0"}
                ],
            },
        ).json()

        # 服务端判题：提交正确选项，客户端谎报 is_correct=false 也应按正确计
        r = c.post(
            "/api/practice/submit",
            headers=headers,
            json={
                "session_id": sess["id"],
                "question_id": 1,
                "answer": "0",
                "is_correct": False,
            },
        ).json()
        assert r["correct"] == 1

        done = c.put(
            f"/api/practice/sessions/{sess['id']}/complete",
            headers=headers,
            json={"weak_points": ["函数"], "strong_points": ["语法"]},
        ).json()
        assert done["passed"] is True

        ov = c.get("/api/progress/overview", headers=headers).json()
        assert ov["module_count"] == 1
        assert "函数" in ov["weak_points"]


def test_engine_gateway_degraded():
    # 未启动 engine 服务时，网关应返回 503 而非崩溃
    with _client() as c:
        token = _auth(c)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        r = c.post(
            "/api/engine/next-review",
            headers=headers,
            json={"knowledge_state": {"topic": "Python", "mastery_level": 0.5}},
        )
        assert r.status_code == 503


def test_review_scheduling_after_practice():
    # 练习完成后应自动生成复习项；引擎不可用时降级排期，功能不中断
    with _client() as c:
        token = _auth(c)
        headers = {"Authorization": f"Bearer {token}"}

        path = c.post("/api/learning/paths", headers=headers,
                      json={"title": "数学", "goal": "学数学"}).json()
        module = c.post("/api/learning/modules", headers=headers,
                        json={"path_id": path["id"], "title": "微积分"}).json()
        sess = c.post("/api/practice/sessions", headers=headers, json={
            "module_id": module["id"],
            "questions": [{"id": 1, "question": "q", "options": ["a"], "answer": "0"}],
        }).json()
        c.post("/api/practice/submit", headers=headers,
               json={"session_id": sess["id"], "question_id": 1, "answer": "0"})
        c.put(f"/api/practice/sessions/{sess['id']}/complete", headers=headers,
              json={"weak_points": ["积分"]})

        due = c.get("/api/review/due", headers=headers).json()
        # 生成 微积分 + 积分 两个复习项（排期在未来 -> upcoming）
        assert due["total"] == 2
        assert due["upcoming_count"] >= 1

        # 复习：提交得分，应更新掌握度与排期
        items = c.get("/api/review/", headers=headers).json()["items"]
        rid = items[0]["id"]
        r = c.post(f"/api/review/{rid}/review", headers=headers,
                   json={"score": 80})
        assert r.status_code == 200
        body = r.json()
        assert body["review_count"] == 1
        assert body["mastery_level"] > 0
