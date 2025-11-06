import time
from typing import Callable, Any

class CircuitBreakerOpenError(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_ts = 0.0

    def _on_success(self):
        self.state = "CLOSED"
        self.failure_count = 0

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_ts = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    async def run(self, coro_func: Callable[..., Any], *args, **kwargs):
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_failure_ts > self.timeout_seconds:
                # half-open
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError("Circuit is open")
        try:
            result = await coro_func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise
