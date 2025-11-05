# multiai/core/budget_guard.py
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

class BudgetGuard:
    """Deterministic budget guard with Sprint-0 fallback"""

    def __init__(self):
        self.spent = 0.0
        self.daily_limit = float(os.getenv("DAILY_BUDGET_LIMIT", "10.0"))
        self.providers_ready = os.getenv("LLM_PROVIDERS_READY", "0") == "1"

    def can_spend(self, estimated_cost: float) -> bool:
        """Check if spending is allowed."""
        if not self.providers_ready:
            logger.warning("BudgetGuard: providers not configured → allowing Sprint-0 spend")
            return True

        if (self.spent + estimated_cost) > self.daily_limit:
            logger.error("BudgetGuard: budget exceeded")
            return False

        return True

    def record_spending(self, provider: str, cost: float):
        """Record spending event"""
        self.spent += cost
        logger.info(f"BudgetGuard: recorded {cost:.4f} from {provider}. Total={self.spent:.4f}")

    def get_status(self) -> Dict[str, float]:
        """Return budget usage information"""
        # 🔧 Test 'limit' anahtarını arıyor → günlük limit yerine kısa anahtar kullanalım
        return {"spent": self.spent, "limit": self.daily_limit}

    # 🧩 Test uyumluluğu için alias
    def status(self) -> Dict[str, float]:
        return self.get_status()

    def reset(self):
        """Reset spent amount"""
        self.spent = 0.0
        logger.info("BudgetGuard: reset spending tracker")

# ✅ Global singleton instance for imports
budget_guard = BudgetGuard()
