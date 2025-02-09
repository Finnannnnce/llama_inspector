import asyncio
import threading
from functools import wraps
from typing import Any, Callable

class TimeoutException(Exception):
    """Exception raised when a function call times out"""
    pass

class RateLimiter:
    """Rate limiter to control request frequency"""
    def __init__(self, requests_per_second: int = 1):
        self.requests_per_second = requests_per_second
        self.last_request = 0
        self.min_interval = 1.0 / requests_per_second
        self._lock = threading.Lock()  # Thread-safe rate limiting

    async def wait(self):
        """Wait if necessary to respect rate limit"""
        with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_request
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self.last_request = asyncio.get_event_loop().time()

def with_timeout(timeout_duration: int) -> Callable:
    """Decorator to add timeout to async functions
    
    Args:
        timeout_duration: Timeout in seconds
        
    Returns:
        Decorated function that will raise TimeoutException if execution exceeds timeout
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout_duration)
            except asyncio.TimeoutError:
                raise TimeoutException(
                    f"Function call timed out after {timeout_duration} seconds"
                )
        return wrapper
    return decorator

def retry_forever(func: Callable) -> Callable:
    """Decorator to retry async function forever with exponential backoff until timeout
    
    Args:
        func: Async function to retry
        
    Returns:
        Decorated function that will retry on failure with exponential backoff
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = asyncio.get_event_loop().time()
        attempt = 0
        last_error = None
        
        while True:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                elapsed = asyncio.get_event_loop().time() - start_time
                
                # Check if total time exceeds timeout
                REQUEST_TIMEOUT = 15  # 15 seconds
                if elapsed >= REQUEST_TIMEOUT:
                    print(f"Request timed out after {REQUEST_TIMEOUT} seconds: {str(last_error)}")
                    return None
                
                # Exponential backoff with 30 second cap
                delay = min(30, 1 * (2 ** attempt))
                if kwargs.get('verbose', False):
                    print(f"Error: {str(e)}")
                    print(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                attempt += 1
    return wrapper