"""进程内滑动窗口限流

注意：状态存进程内存，多 worker 部署时每个进程独立计数（够用于单机部署；
跨进程精确限流需要 Redis，属后续扩展）。
"""
import time
from collections import defaultdict, deque
from typing import Callable


class SlidingWindowLimiter:
    """按 key 的滑动窗口计数器：window_seconds 内最多 max_events 次"""

    def __init__(self, max_events: int, window_seconds: float,
                 clock: Callable[[], float] = time.monotonic):
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._clock = clock
        self._events: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = self._clock()
        window_start = now - self.window_seconds
        events = self._events[key]
        while events and events[0] <= window_start:
            events.popleft()
        if len(events) >= self.max_events:
            return False
        events.append(now)
        return True

    def retry_after_seconds(self, key: str) -> float:
        """距窗口内最早事件过期的秒数（配合 429 Retry-After 头）"""
        events = self._events.get(key)
        if not events:
            return 0.0
        return max(0.0, events[0] + self.window_seconds - self._clock())
