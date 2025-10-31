# BudgetGuard — Sprint C
import threading

class BudgetGuard:
    def __init__(self, monthly_limit_usd: float):
        self.lock = threading.Lock()
        self.limit = monthly_limit_usd
        self.spent = 0.0

    def reserve(self, estimate_usd: float) -> bool:
        with self.lock:
            if self.spent + estimate_usd > self.limit:
                return False
            self.spent += estimate_usd
            return True

    def release(self, estimate_usd: float):
        with self.lock:
            self.spent = max(0.0, self.spent - estimate_usd)
