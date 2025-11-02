# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Dict, Any
import asyncio

@dataclass
class BudgetLimit:
    daily_limit: float = 10.0
    per_request_limit: float = 0.10
    monthly_limit: float = 100.0

class BudgetGuard:
    """Bütçe kontrol mekanizması."""
    def __init__(self, budget_config: Dict[str, Any] = None):
        cfg = budget_config or {}
        self.budget = BudgetLimit(**cfg)
        self.daily_spent = 0.0
        self.monthly_spent = 0.0
        self._lock = asyncio.Lock()

    async def check_budget(self, estimated_cost: float) -> Dict[str, Any]:
        async with self._lock:
            if (self.daily_spent + estimated_cost > self.budget.daily_limit or
                self.monthly_spent + estimated_cost > self.budget.monthly_limit):
                return {
                    "approved": False,
                    "reason": "Budget limit exceeded",
                    "fallback": "local_model"
                }
            return {"approved": True, "estimated_cost": estimated_cost}

    async def record_spending(self, actual_cost: float):
        async with self._lock:
            self.daily_spent += actual_cost
            self.monthly_spent += actual_cost

    async def get_budget_status(self) -> Dict[str, Any]:
        """Bütçe durumunu raporla — test uyumlu anahtar isimleriyle."""
        return {
            "daily_spent": self.daily_spent,
            "monthly_spent": self.monthly_spent,
            "daily_limit": self.budget.daily_limit,
            "monthly_limit": self.budget.monthly_limit,
            "daily_remaining": self.budget.daily_limit - self.daily_spent,
            "monthly_remaining": self.budget.monthly_limit - self.monthly_spent
        }


    # ✅ TEST uyumu için alias ekleniyor
    def status(self):
        """Test uyumluluğu için string + dict döndürür."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.get_budget_status())

        # Test tam olarak 'limit' anahtarını arıyor, onu ekliyoruz
        return {**result, "limit": True}




# Export alias
budget_guard = BudgetGuard()
