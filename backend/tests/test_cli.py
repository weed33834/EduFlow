"""统一 CLI 测试：create-user / stats（ingest/traces 已有独立用例）"""
import asyncio
import importlib.util
import uuid
from pathlib import Path

import pytest


def _load_cli():
    spec = importlib.util.spec_from_file_location(
        "eduagent_cli", Path(__file__).resolve().parents[1] / "scripts" / "cli.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module", autouse=True)
def _db():
    from tests.conftest import client  # noqa: F401 触发建表
    yield


def test_create_user_then_login(client):
    mod = _load_cli()
    suffix = uuid.uuid4().hex[:8]

    async def run():
        return await mod.cmd_create_user(_Args(
            email=f"cli-{suffix}@example.com",
            username=f"cli{suffix}",
            password="password123",
            display_name="CLI 用户",
        ))

    assert asyncio.run(run()) == 0

    # 用同一凭据走 API 登录 → 密码哈希正确、画像已创建
    login = client.post("/api/auth/login", json={
        "email": f"cli-{suffix}@example.com",
        "password": "password123",
    })
    assert login.status_code == 200

    # 重复创建必须失败（exit code 1）
    async def rerun():
        return await mod.cmd_create_user(_Args(
            email=f"cli-{suffix}@example.com",
            username=f"cli{suffix}x",
            password="password123",
            display_name=None,
        ))
    assert asyncio.run(rerun()) == 1


def test_stats_returns_counts(client, auth_headers):
    """注册+对话后 stats 应有非零数据"""
    resp = client.post("/api/chat", json={"message": "你好"}, headers=auth_headers)
    assert resp.status_code == 200

    mod = _load_cli()
    stats = asyncio.run(mod.cmd_stats(_Args()))
    assert stats["users"] >= 1
    assert stats["sessions"] >= 1
    assert stats["messages"] >= 2  # user + assistant
    assert isinstance(stats["review_due_now"], int)


class _Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
