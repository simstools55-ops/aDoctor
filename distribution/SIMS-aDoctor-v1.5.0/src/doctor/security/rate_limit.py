from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta, timezone


class RateLimitError(RuntimeError):
    pass


class InMemoryRateLimiter:
    def __init__(self, *, requests_per_minute: int, burst: int) -> None:
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self._requests: dict[str, deque[datetime]] = {}

    def check(self, client_id: str) -> None:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=1)
        queue = self._requests.setdefault(client_id, deque())
        while queue and queue[0] <= window_start:
            queue.popleft()
        if len(queue) >= self.requests_per_minute + self.burst:
            raise RateLimitError("Rate limit exceeded")
        queue.append(now)
