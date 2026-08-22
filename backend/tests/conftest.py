"""测试环境配置 — 必须在导入 app 之前设置环境变量"""
import os
import tempfile

_TEST_DB = os.path.join(tempfile.gettempdir(), "eduagent_test.db")
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB}"
os.environ["JWT_SECRET"] = "test-secret-not-for-production"
os.environ["LITELLM_API_KEY"] = ""
os.environ["ENV"] = "dev"

import pytest
from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    import uuid
    suffix = uuid.uuid4().hex[:8]
    resp = client.post("/api/auth/register", json={
        "email": f"stu-{suffix}@example.com",
        "username": f"stu{suffix}",
        "password": "password123",
    })
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def parse_sse_events(text: str) -> list[dict]:
    """把 SSE 文本解析为事件字典列表（跳过 [done] 哨兵）"""
    events = []
    for block in text.split("\n\n"):
        for line in block.splitlines():
            if line.startswith("data: ") and line != "data: [done]":
                events.append(__import__("json").loads(line[len("data: "):]))
    return events


def find_complete(events: list[dict]) -> dict:
    completes = [e for e in events if e.get("type") == "complete"]
    assert completes, f"缺少 complete 事件，实际事件类型: {[e.get('type') for e in events]}"
    return completes[-1]
