"""限流：进程内滑动窗口 + 可选 Redis 分布式滑动窗口

- SlidingWindowLimiter（默认）：状态存进程内存，单机部署够用
- RedisSlidingWindowLimiter：配置 REDIS_URL 时启用，ZSET 实现跨 worker 精确计数；
  Redis 不可用时自动回退内存实现（fail-open，保证可用性优先）
"""
import logging
import time
import uuid
from collections import defaultdict, deque
from typing import Callable

from app.config import settings

logger = logging.getLogger(__name__)


class SlidingWindowLimiter:
    """按 key 的滑动窗口计数器：window_seconds 内最多 max_events 次"""

    def __init__(self, max_events: int, window_seconds: float,
                 clock: Callable[[], float] = time.monotonic):
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._clock = clock
        self._events: dict[str, deque] = defaultdict(deque)

    async def allow(self, key: str) -> bool:
        now = self._clock()
        window_start = now - self.window_seconds
        events = self._events[key]
        while events and events[0] <= window_start:
            events.popleft()
        if len(events) >= self.max_events:
            return False
        events.append(now)
        return True

    async def retry_after_seconds(self, key: str) -> float:
        """距窗口内最早事件过期的秒数（配合 429 Retry-After 头）"""
        events = self._events.get(key)
        if not events:
            return 0.0
        return max(0.0, events[0] + self.window_seconds - self._clock())


class RedisSlidingWindowLimiter:
    """Redis ZSET 滑动窗口（异步）。接口与 SlidingWindowLimiter 一致。

    - score/member 都用毫秒时间戳，member 加随机后缀避免同毫秒覆盖
    - Redis 故障时 fail-open 放行并记 warning（可用性优先于精确限流）
    """

    def __init__(self, redis_client, max_events: int, window_seconds: float,
                 clock: Callable[[], float] = time.monotonic):
        self.redis = redis_client
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._clock = clock
        self.prefix = "ratelimit"

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}:{self.max_events}:{key}"

    async def allow(self, key: str) -> bool:
        now_ms = int(self._clock() * 1000)
        window_ms = int(self.window_seconds * 1000)
        full_key = self._full_key(key)
        # 成员必须全局唯一：同毫秒并发下 zadd 是按 member 覆盖语义
        member = f"{now_ms}:{uuid.uuid4().hex}"
        try:
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(full_key, 0, now_ms - window_ms)
            pipe.zcard(full_key)
            pipe.zadd(full_key, {member: now_ms})
            pipe.expire(full_key, max(1, int(self.window_seconds) + 1))
            _, count, _, _ = await pipe.execute()
        except Exception:
            logger.warning("限流 Redis 不可用，放行（fail-open）", exc_info=True)
            return True
        if count >= self.max_events:
            # 已到上限：撤掉刚写入的成员，保持窗口干净
            try:
                await self.redis.zrem(full_key, member)
            except Exception:
                pass
            return False
        return True

    async def retry_after_seconds(self, key: str) -> float:
        full_key = self._full_key(key)
        try:
            oldest = await self.redis.zrange(full_key, 0, 0, withscores=True)
        except Exception:
            return 0.0
        if not oldest:
            return 0.0
        oldest_ms = float(oldest[0][1])
        remaining = (oldest_ms + self.window_seconds * 1000 - self._clock() * 1000) / 1000
        return max(0.0, remaining)


def build_limiter(max_events: int, window_seconds: float):
    """按 REDIS_URL 配置选择实现：配了就用 Redis，没配/初始化失败退内存"""
    url = (settings.REDIS_URL or "").strip()
    if not url:
        return SlidingWindowLimiter(max_events, window_seconds)
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(url, decode_responses=True)
        limiter = RedisSlidingWindowLimiter(client, max_events, window_seconds)
        logger.info("限流使用 Redis 后端 url=%s", url)
        return limiter
    except Exception:
        logger.warning("Redis 限流初始化失败，回退进程内实现", exc_info=True)
        return SlidingWindowLimiter(max_events, window_seconds)
