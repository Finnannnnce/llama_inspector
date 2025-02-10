import asyncio
import time
from typing import Optional
from dataclasses import dataclass, field
from collections import deque

@dataclass
class RateLimiter:
    """Rate limiter for API calls with async support"""
    calls_per_second: int
    window_size: float = 1.0
    _calls: deque = field(default_factory=lambda: deque(maxlen=1000))
    _lock: Optional[asyncio.Lock] = None

    def __post_init__(self):
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass

    async def acquire(self):
        """Acquire rate limit slot"""
        async with self._lock:
            now = time.time()
            
            # Remove old calls outside window
            while self._calls and now - self._calls[0] > self.window_size:
                self._calls.popleft()
            
            # Wait if at limit
            if len(self._calls) >= self.calls_per_second:
                sleep_time = self._calls[0] + self.window_size - now
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            # Add current call
            self._calls.append(now)

    def reset(self):
        """Reset rate limiter state"""
        self._calls.clear()