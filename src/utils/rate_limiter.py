import asyncio
import time

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.interval = 60.0 / max(1, requests_per_minute)
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def acquire(self):
        async with self._lock:
            now = time.time()
            wait = self._last + self.interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.time()
