import time, threading
class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate; self.capacity = capacity
        self.tokens = capacity; self.lock = threading.Lock()
        self.last = time.time()
    def allow(self) -> bool:
        with self.lock:
            now = time.time(); elapsed = now - self.last
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last = now
            if self.tokens >= 1: self.tokens -= 1; return True
            return False
