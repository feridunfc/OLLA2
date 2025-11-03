# multiai/agents/budget_guard_agent.py
from __future__ import annotations
import time
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from prometheus_client import Counter, Gauge, Histogram

from ..core.policy_agent import policy_agent
from ..utils.observability import metrics

logger = logging.getLogger("budget_guard")


class BudgetAlertLevel(Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    BLOCKED = "blocked"


@dataclass
class CostBreakdown:
    """Detaylı maliyet analizi sınıfı"""
    cloud_costs: Dict[str, float] = field(default_factory=dict)  # provider -> cost
    local_costs: float = 0.0
    infrastructure_costs: float = 0.0
    storage_costs: float = 0.0

    @property
    def total_cloud_cost(self) -> float:
        return sum(self.cloud_costs.values())

    @property
    def total_cost(self) -> float:
        return self.total_cloud_cost + self.local_costs + self.infrastructure_costs + self.storage_costs


class EnhancedBudgetGuardAgent:
    """
    V5.0 Enhanced Budget Guard Agent
    Gelişmiş bütçe izleme, maliyet optimizasyonu ve çok katmanlı limit yönetimi
    """

    def __init__(self, policy_agent_instance=None):
        self.policy_agent = policy_agent_instance or policy_agent
        self.budget_policy = self.policy_agent.budget_policy

        # Bütçe durumu
        self.total_budget_usd = self.budget_policy.monthly_limit
        self.used_budget_usd = 0.0
        self.daily_budget = self.budget_policy.daily_limit
        self.daily_used = 0.0

        # Detaylı maliyet takibi
        self.cost_breakdown = CostBreakdown()
        self.session_costs: List[Dict[str, Any]] = []
        self.monthly_history: List[Dict[str, Any]] = []

        # Zaman bazlı reset
        self.last_reset_date = datetime.now().date()
        self.current_month = datetime.now().month

        # Metrikler
        self.budget_usage_metric = Gauge('multiai_budget_usage_percent', 'Budget utilization percentage')
        self.cost_metric = Counter('multiai_cost_total', 'Total cost incurred', ['provider', 'model'])
        self.alert_metric = Counter('multiai_budget_alerts_total', 'Budget alerts triggered', ['level'])

        # Alert geçmişi
        self.alert_history: List[Dict[str, Any]] = []

        logger.info(f"BudgetGuard initialized with ${self.total_budget_usd} monthly budget")

    async def record_llm_usage(self, model: str, provider: str, tokens_used: int,
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        LLM kullanımını kaydet ve maliyet hesapla
        """
        context = context or {}
        task_type = context.get("task_type", "general")
        complexity = context.get("complexity", "medium")

        try:
            # Maliyet hesapla
            cost_details = await self._calculate_cost(model, provider, tokens_used, task_type, complexity)
            total_cost = cost_details["total_cost"]

            # Bütçe kontrolü
            budget_check = await self._check_budget_limits(total_cost, provider, model)

            if not budget_check["allowed"]:
                await self._trigger_alert(BudgetAlertLevel.BLOCKED, budget_check["reason"])
                return {
                    "recorded": False,
                    "reason": budget_check["reason"],
                    "suggested_action": budget_check.get("suggested_action", "use_local"),
                    "fallback_available": True
                }

            # Kullanımı kaydet
            await self._record_usage(model, provider, tokens_used, total_cost, cost_details, context)

            # Alert kontrolü
            if budget_check.get("warning"):
                await self._trigger_alert(BudgetAlertLevel.WARNING, budget_check["warning"])

            # Metrikleri güncelle
            self._update_metrics(model, provider, total_cost)

            logger.info(f"Recorded {provider}.{model} usage: ${total_cost:.6f}")

            return {
                "recorded": True,
                "cost": total_cost,
                "cost_breakdown": cost_details,
                "budget_remaining": self.remaining_budget,
                "daily_remaining": self.daily_budget - self.daily_used,
                "utilization": self.utilization
            }

        except Exception as e:
            logger.error(f"Failed to record LLM usage: {e}")
            return {"recorded": False, "error": str(e)}

    async def _calculate_cost(self, model: str, provider: str, tokens: int,
                              task_type: str, complexity: str) -> Dict[str, Any]:
        """Detaylı maliyet hesaplama"""

        # Model bazlı fiyatlandırma
        pricing = await self._get_model_pricing(model, provider)

        # Token sayısını adjust et (complexity'e göre)
        adjusted_tokens = self._adjust_token_count(tokens, complexity, task_type)

        # Maliyet hesapla
        input_cost = (adjusted_tokens["input"] / 1000) * pricing["input_per_1k"]
        output_cost = (adjusted_tokens["output"] / 1000) * pricing["output_per_1k"]
        total_cost = input_cost + output_cost

        # Infrastructure overhead ekle
        overhead = total_cost * 0.05  # %5 infrastructure overhead

        return {
            "total_cost": total_cost + overhead,
            "breakdown": {
                "input_tokens": adjusted_tokens["input"],
                "output_tokens": adjusted_tokens["output"],
                "input_cost": input_cost,
                "output_cost": output_cost,
                "infrastructure_overhead": overhead,
                "pricing_model": pricing
            },
            "adjusted_tokens": adjusted_tokens,
            "provider": provider,
            "model": model
        }

    async def _get_model_pricing(self, model: str, provider: str) -> Dict[str, float]:
        """Model fiyatlandırmasını al"""

        # Gerçek fiyatlandırma verileri (güncel tutulmalı)
        pricing_data = {
            "openai": {
                "gpt-4": {"input_per_1k": 0.03, "output_per_1k": 0.06},
                "gpt-4-turbo": {"input_per_1k": 0.01, "output_per_1k": 0.03},
                "gpt-3.5-turbo": {"input_per_1k": 0.0015, "output_per_1k": 0.002},
            },
            "anthropic": {
                "claude-3-opus": {"input_per_1k": 0.015, "output_per_1k": 0.075},
                "claude-3-sonnet": {"input_per_1k": 0.003, "output_per_1k": 0.015},
                "claude-3-haiku": {"input_per_1k": 0.00025, "output_per_1k": 0.00125},
            },
            "local": {
                "llama2": {"input_per_1k": 0.0, "output_per_1k": 0.0},
                "codellama": {"input_per_1k": 0.0, "output_per_1k": 0.0},
            }
        }

        provider_pricing = pricing_data.get(provider, {})
        model_pricing = provider_pricing.get(model, {"input_per_1k": 0.01, "output_per_1k": 0.02})

        return model_pricing

    def _adjust_token_count(self, tokens: int, complexity: str, task_type: str) -> Dict[str, int]:
        """Görev karmaşıklığına göre token sayısını adjust et"""

        # Varsayılan dağılım: %70 input, %30 output
        base_input = int(tokens * 0.7)
        base_output = int(tokens * 0.3)

        # Complexity adjustment
        complexity_multipliers = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.3,
            "critical": 1.6
        }

        multiplier = complexity_multipliers.get(complexity, 1.0)

        # Task type adjustment
        if task_type in ["research", "analysis"]:
            # Daha fazla output
            input_ratio, output_ratio = 0.6, 0.4
        elif task_type in ["coding", "debugging"]:
            # Dengeli
            input_ratio, output_ratio = 0.7, 0.3
        else:
            input_ratio, output_ratio = 0.7, 0.3

        return {
            "input": int(base_input * multiplier * input_ratio),
            "output": int(base_output * multiplier * output_ratio)
        }

    async def _check_budget_limits(self, cost: float, provider: str, model: str) -> Dict[str, Any]:
        """Çok katmanlı bütçe limit kontrolü"""

        # Günlük reset kontrolü
        await self._check_daily_reset()

        # Kritik limit kontrolü
        if self.used_budget_usd + cost > self.total_budget_usd:
            return {
                "allowed": False,
                "reason": f"Monthly budget exceeded: ${self.used_budget_usd:.2f} + ${cost:.2f} > ${self.total_budget_usd:.2f}",
                "suggested_action": "use_local_or_fallback"
            }

        # Günlük limit kontrolü
        if self.daily_used + cost > self.daily_budget:
            return {
                "allowed": False,
                "reason": f"Daily budget exceeded: ${self.daily_used:.2f} + ${cost:.2f} > ${self.daily_budget:.2f}",
                "suggested_action": "defer_until_tomorrow"
            }

        # Kritik uyarı seviyesi
        remaining_monthly = self.total_budget_usd - self.used_budget_usd
        if remaining_monthly <= self.budget_policy.critical_alert:
            return {
                "allowed": True,
                "warning": f"Critical budget level: ${remaining_monthly:.2f} remaining"
            }

        # Cost optimization önerisi
        if provider != "local" and cost > 0.1:  # $0.1'den büyük cloud maliyetleri
            local_equivalent = await self._get_local_equivalent_cost(model, cost)
            if local_equivalent and local_equivalent < cost * 0.5:
                return {
                    "allowed": True,
                    "warning": f"Consider using local model: ${cost:.4f} vs ${local_equivalent:.4f}",
                    "optimization_suggestion": "use_local"
                }

        return {"allowed": True}

    async def _get_local_equivalent_cost(self, model: str, cloud_cost: float) -> Optional[float]:
        """Local model equivalent cost hesapla"""
        # Local modeller için sadece infrastructure maliyeti
        # Bu örnekte sabit bir değer kullanıyoruz
        local_infrastructure_cost = 0.0001  # $0.0001 per request

        # Model complexity adjustment
        model_complexity = {
            "gpt-4": 2.0,
            "gpt-3.5-turbo": 1.0,
            "claude-3-opus": 2.5,
            "claude-3-sonnet": 1.5,
            "claude-3-haiku": 0.8
        }

        complexity = model_complexity.get(model, 1.0)
        return local_infrastructure_cost * complexity

    async def _record_usage(self, model: str, provider: str, tokens: int,
                            total_cost: float, cost_details: Dict, context: Dict):
        """Kullanımı detaylı şekilde kaydet"""

        usage_record = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "provider": provider,
            "tokens_used": tokens,
            "total_cost": total_cost,
            "cost_breakdown": cost_details["breakdown"],
            "task_type": context.get("task_type", "general"),
            "complexity": context.get("complexity", "medium"),
            "artifact_id": context.get("artifact_id"),
            "sprint_id": context.get("sprint_id")
        }

        # Toplam maliyetleri güncelle
        self.used_budget_usd += total_cost
        self.daily_used += total_cost

        # Cost breakdown'ı güncelle
        if provider == "local":
            self.cost_breakdown.local_costs += total_cost
        else:
            if provider not in self.cost_breakdown.cloud_costs:
                self.cost_breakdown.cloud_costs[provider] = 0.0
            self.cost_breakdown.cloud_costs[provider] += total_cost

        # Session geçmişine ekle
        self.session_costs.append(usage_record)

        # Son 1000 kayıt tut
        if len(self.session_costs) > 1000:
            self.session_costs = self.session_costs[-1000:]

    async def _check_daily_reset(self):
        """Günlük bütçeyi resetle"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_used = 0.0
            self.last_reset_date = current_date
            logger.info("Daily budget reset")

        # Aylık reset kontrolü
        current_month = datetime.now().month
        if current_month != self.current_month:
            await self._monthly_reset()

    async def _monthly_reset(self):
        """Aylık bütçeyi resetle ve geçmişi kaydet"""
        monthly_summary = {
            "month": self.current_month,
            "year": datetime.now().year,
            "total_used": self.used_budget_usd,
            "cost_breakdown": self.cost_breakdown.cloud_costs.copy(),
            "session_count": len(self.session_costs)
        }

        self.monthly_history.append(monthly_summary)

        # Reset values
        self.used_budget_usd = 0.0
        self.daily_used = 0.0
        self.cost_breakdown = CostBreakdown()
        self.session_costs = []
        self.current_month = datetime.now().month

        logger.info(f"Monthly budget reset. History: {len(self.monthly_history)} months")

    async def _trigger_alert(self, level: BudgetAlertLevel, message: str):
        """Bütçe alert'ı tetikle"""
        alert_record = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "message": message,
            "budget_used": self.used_budget_usd,
            "budget_remaining": self.remaining_budget,
            "utilization": self.utilization
        }

        self.alert_history.append(alert_record)
        self.alert_metric.labels(level=level.value).inc()

        # Log seviyesi
        log_level = {
            BudgetAlertLevel.NORMAL: logger.info,
            BudgetAlertLevel.WARNING: logger.warning,
            BudgetAlertLevel.CRITICAL: logger.error,
            BudgetAlertLevel.BLOCKED: logger.critical
        }

        log_level[level](f"Budget Alert [{level.value}]: {message}")

        # External notification (n8n entegrasyonu)
        if level in [BudgetAlertLevel.CRITICAL, BudgetAlertLevel.BLOCKED]:
            await self._send_external_alert(alert_record)

    async def _send_external_alert(self, alert: Dict[str, Any]):
        """n8n veya diğer external sistemlere alert gönder"""
        try:
            # n8n webhook entegrasyonu
            # Bu kısım n8n configuration'una göre doldurulacak
            webhook_url = "https://your-n8n-instance.com/webhook/budget-alert"
            alert_data = {
                "alert": alert,
                "budget_status": self.report(),
                "timestamp": datetime.now().isoformat()
            }

            # HTTP request gönder
            # await self._send_webhook(webhook_url, alert_data)
            logger.info(f"External alert prepared for n8n: {alert['level']}")

        except Exception as e:
            logger.error(f"Failed to send external alert: {e}")

    def _update_metrics(self, model: str, provider: str, cost: float):
        """Prometheus metriklerini güncelle"""
        self.budget_usage_metric.set(self.utilization)
        self.cost_metric.labels(provider=provider, model=model).inc(cost)

    @property
    def utilization(self) -> float:
        """Bütçe kullanım yüzdesi"""
        if self.total_budget_usd == 0:
            return 0.0
        return min(100.0, (self.used_budget_usd / self.total_budget_usd) * 100.0)

    @property
    def remaining_budget(self) -> float:
        """Kalan bütçe"""
        return max(0.0, self.total_budget_usd - self.used_budget_usd)

    @property
    def daily_utilization(self) -> float:
        """Günlük bütçe kullanımı"""
        if self.daily_budget == 0:
            return 0.0
        return min(100.0, (self.daily_used / self.daily_budget) * 100.0)

    def get_cost_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Maliyet optimizasyon önerileri"""
        suggestions = []

        # Cloud maliyetleri yüksekse local öner
        cloud_ratio = self.cost_breakdown.total_cloud_cost / self.cost_breakdown.total_cost if self.cost_breakdown.total_cost > 0 else 0
        if cloud_ratio > 0.8:
            suggestions.append({
                "type": "use_more_local",
                "priority": "high",
                "description": f"{cloud_ratio:.1%} of costs are from cloud providers",
                "estimated_savings": self.cost_breakdown.total_cloud_cost * 0.7  # %70 tasarruf
            })

        # Günlük limit yakınsa zamanlama öner
        if self.daily_utilization > 80:
            suggestions.append({
                "type": "schedule_tasks",
                "priority": "medium",
                "description": f"Daily budget {self.daily_utilization:.1f}% used",
                "suggestion": "Schedule non-critical tasks for tomorrow"
            })

        return suggestions

    def report(self) -> Dict[str, Any]:
        """Detaylı bütçe raporu"""
        return {
            "budget": {
                "total_monthly_usd": self.total_budget_usd,
                "used_usd": self.used_budget_usd,
                "remaining_usd": self.remaining_budget,
                "utilization_percent": self.utilization,
                "daily_budget": self.daily_budget,
                "daily_used": self.daily_used,
                "daily_utilization": self.daily_utilization
            },
            "cost_breakdown": {
                "cloud_costs": self.cost_breakdown.cloud_costs,
                "local_costs": self.cost_breakdown.local_costs,
                "total_cloud": self.cost_breakdown.total_cloud_cost,
                "total_cost": self.cost_breakdown.total_cost
            },
            "optimization_suggestions": self.get_cost_optimization_suggestions(),
            "recent_usage": self.session_costs[-10:],  # Son 10 kullanım
            "alert_status": self.alert_history[-5:] if self.alert_history else [],  # Son 5 alert
            "monthly_history_count": len(self.monthly_history)
        }

    async def forecast_usage(self, days: int = 30) -> Dict[str, Any]:
        """Gelecek kullanım tahmini"""
        if not self.session_costs:
            return {"forecast": "insufficient_data"}

        # Basit lineer tahmin
        daily_avg = self.used_budget_usd / max(1, len(self.session_costs)) * 10  # Basit ortalama

        forecast = {
            "period_days": days,
            "current_daily_average": daily_avg,
            "projected_usage": daily_avg * days,
            "budget_remaining": self.remaining_budget,
            "days_until_exhaustion": self.remaining_budget / daily_avg if daily_avg > 0 else float('inf'),
            "recommendation": "within_budget" if daily_avg * days < self.remaining_budget else "exceeds_budget"
        }

        return forecast

    def to_json(self) -> str:
        """JSON raporu"""
        return json.dumps(self.report(), indent=2, default=str)

    async def emergency_stop(self) -> Dict[str, Any]:
        """Acil durdurma - tüm cloud harcamalarını bloke et"""
        stop_result = {
            "emergency_stop_activated": True,
            "timestamp": datetime.now().isoformat(),
            "final_budget_status": self.report(),
            "affected_providers": list(self.cost_breakdown.cloud_costs.keys())
        }

        # Alert gönder
        await self._trigger_alert(BudgetAlertLevel.BLOCKED, "EMERGENCY STOP: All cloud spending blocked")

        logger.critical("EMERGENCY STOP ACTIVATED - All cloud spending blocked")

        return stop_result


# Global instance
budget_guard_agent = EnhancedBudgetGuardAgent()