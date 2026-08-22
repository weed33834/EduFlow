"""限流器单元测试 + API 429 集成测试"""
import asyncio

from app.ratelimit import SlidingWindowLimiter
from app.routers.auth import auth_limiter
from app.routers.chat import chat_limiter


def test_allows_within_limit():
    t = [100.0]
    limiter = SlidingWindowLimiter(max_events=3, window_seconds=10, clock=lambda: t[0])
    assert limiter.allow("k")
    assert limiter.allow("k")
    assert limiter.allow("k")
    assert not limiter.allow("k")


def test_window_slides():
    t = [100.0]
    limiter = SlidingWindowLimiter(max_events=2, window_seconds=10, clock=lambda: t[0])
    assert limiter.allow("k")
    assert limiter.allow("k")
    assert not limiter.allow("k")
    t[0] += 11.0  # 窗口滑过
    assert limiter.allow("k")


def test_keys_are_isolated():
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=10)
    assert limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")


def test_retry_after_seconds():
    t = [100.0]
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=10, clock=lambda: t[0])
    limiter.allow("k")
    assert not limiter.allow("k")
    retry = limiter.retry_after_seconds("k")
    assert 0 < retry <= 10


def test_chat_endpoint_returns_429_when_limited(client, auth_headers, monkeypatch):
    """预填充限流器到上限后，chat 必须返回 429 且带 Retry-After"""
    from app.routers import chat as chat_router

    user_id = client.get("/api/auth/me", headers=auth_headers).json()["id"]
    key = f"user:{user_id}"
    for _ in range(chat_router.settings.RATE_LIMIT_CHAT_PER_MIN):
        chat_router.chat_limiter.allow(key)

    resp = client.post("/api/chat", json={"message": "hi"}, headers=auth_headers)
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers

    # 清理，避免影响其他用例
    chat_router.chat_limiter._events.pop(key, None)


def test_login_endpoint_rate_limited(client):
    """登录接口按 IP 限流：填满后返回 429"""
    for _ in range(auth_limiter.max_events):
        auth_limiter.allow("ip:testclient")

    resp = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 429

    auth_limiter._events.pop("ip:testclient", None)


def test_async_allow_not_blocking_event_loop():
    """限流判断是纯同步内存操作，不应抛异常"""
    async def run():
        limiter = SlidingWindowLimiter(max_events=5, window_seconds=60)
        return all(limiter.allow(f"u{i}") for i in range(5))
    assert asyncio.run(run())
