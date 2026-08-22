"""限流测试：内存实现（同步时钟可控）+ Redis 实现（fakeredis）+ API 429 集成"""
import asyncio

import pytest

from app.ratelimit import (
    RedisSlidingWindowLimiter,
    SlidingWindowLimiter,
    build_limiter,
)
from app.routers.auth import auth_limiter
from app.routers.chat import chat_limiter


# ── 内存实现 ──────────────────────────────────────────────


def test_memory_allows_within_limit():
    t = [100.0]
    limiter = SlidingWindowLimiter(max_events=3, window_seconds=10, clock=lambda: t[0])
    async def run():
        return [await limiter.allow("k") for _ in range(4)]
    results = asyncio.run(run())
    assert results == [True, True, True, False]


def test_memory_window_slides():
    t = [100.0]
    limiter = SlidingWindowLimiter(max_events=2, window_seconds=10, clock=lambda: t[0])

    async def run():
        r = [await limiter.allow("k"), await limiter.allow("k")]
        t[0] += 11.0
        r.append(await limiter.allow("k"))
        return r

    assert asyncio.run(run()) == [True, True, True]


def test_memory_keys_isolated():
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=10)

    async def run():
        a1 = await limiter.allow("a")
        a2 = await limiter.allow("a")
        b1 = await limiter.allow("b")
        return a1, a2, b1

    assert asyncio.run(run()) == (True, False, True)


def test_memory_retry_after_seconds():
    t = [100.0]
    limiter = SlidingWindowLimiter(max_events=1, window_seconds=10, clock=lambda: t[0])

    async def run():
        await limiter.allow("k")
        ok = await limiter.allow("k")
        retry = await limiter.retry_after_seconds("k")
        return ok, retry

    ok, retry = asyncio.run(run())
    assert ok is False
    assert 0 < retry <= 10


# ── Redis 实现（fakeredis 验证真实 ZSET 管线逻辑） ────────────


@pytest.fixture()
def fake_redis():
    from fakeredis import aioredis as fake_aioredis
    client = fake_aioredis.FakeRedis(decode_responses=True)
    yield client
    asyncio.run(client.aclose())


def test_redis_allows_within_limit(fake_redis):
    limiter = RedisSlidingWindowLimiter(fake_redis, max_events=3, window_seconds=10)

    async def run():
        return [await limiter.allow("u1") for _ in range(4)]

    assert asyncio.run(run()) == [True, True, True, False]


def test_redis_window_slides(fake_redis):
    t = [1000.0]
    limiter = RedisSlidingWindowLimiter(
        fake_redis, max_events=2, window_seconds=10, clock=lambda: t[0],
    )

    async def run():
        r = [await limiter.allow("u1"), await limiter.allow("u1")]
        assert await limiter.allow("u1") is False
        t[0] += 11.0
        r.append(await limiter.allow("u1"))
        return r

    assert asyncio.run(run()) == [True, True, True]


def test_redis_isolated_between_users(fake_redis):
    limiter = RedisSlidingWindowLimiter(fake_redis, max_events=1, window_seconds=60)

    async def run():
        a = await limiter.allow("alice")
        a2 = await limiter.allow("alice")
        b = await limiter.allow("bob")
        return a, a2, b

    assert asyncio.run(run()) == (True, False, True)


def test_redis_fail_open_on_error(fake_redis):
    class BrokenClient:
        def pipeline(self):
            raise RuntimeError("redis down")

    limiter = RedisSlidingWindowLimiter(BrokenClient(), max_events=1, window_seconds=10)
    assert asyncio.run(limiter.allow("anyone")) is True, "Redis 挂掉应放行（fail-open）"


def test_redis_retry_after(fake_redis):
    t = [1000.0]
    limiter = RedisSlidingWindowLimiter(
        fake_redis, max_events=1, window_seconds=10, clock=lambda: t[0],
    )

    async def run():
        await limiter.allow("u1")
        denied = await limiter.allow("u1")
        retry = await limiter.retry_after_seconds("u1")
        return denied, retry

    denied, retry = asyncio.run(run())
    assert denied is False
    assert 0 < retry <= 10


# ── 工厂 ─────────────────────────────────────────────────


def test_build_limiter_defaults_to_memory(monkeypatch):
    monkeypatch.setattr("app.ratelimit.settings.REDIS_URL", "")
    assert isinstance(build_limiter(5, 60), SlidingWindowLimiter)


def test_build_limiter_uses_redis_when_configured(monkeypatch, fake_redis):
    import app.ratelimit as rl
    monkeypatch.setattr(rl.settings, "REDIS_URL", "redis://localhost:6379/0")

    captured = {}
    def fake_from_url(url, decode_responses=True):
        captured["url"] = url
        return fake_redis

    import redis.asyncio as aioredis
    monkeypatch.setattr(aioredis, "from_url", fake_from_url)

    limiter = build_limiter(5, 60)
    assert isinstance(limiter, RedisSlidingWindowLimiter)
    assert captured["url"] == "redis://localhost:6379/0"


# ── API 集成：429 + Retry-After ──────────────────────────


def test_chat_endpoint_returns_429_when_limited(client, auth_headers):
    from app.routers import chat as chat_router

    user_id = client.get("/api/auth/me", headers=auth_headers).json()["id"]
    key = f"user:{user_id}"

    async def fill():
        for _ in range(chat_router.chat_limiter.max_events):
            await chat_router.chat_limiter.allow(key)

    asyncio.run(fill())

    resp = client.post("/api/chat", json={"message": "hi"}, headers=auth_headers)
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers

    if hasattr(chat_router.chat_limiter, "_events"):
        chat_router.chat_limiter._events.pop(key, None)


def test_login_endpoint_rate_limited(client):
    async def fill():
        for _ in range(auth_limiter.max_events):
            await auth_limiter.allow("ip:testclient")

    asyncio.run(fill())

    resp = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 429

    if hasattr(auth_limiter, "_events"):
        auth_limiter._events.pop("ip:testclient", None)
