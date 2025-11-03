
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from .policy_agent import policy_agent
from .budget_guard import budget_guard
from ..utils.robust_ollama_client import RobustOllamaClient
from .cloud_clients.openai_client import OpenAIClient
from .cloud_clients.anthropic_client import AnthropicClient

logger = logging.getLogger("multiai.hybrid_router")
logger.setLevel(logging.INFO)


@dataclass
class RoutingDecision:
    use_cloud: bool
    provider: str
    model_name: str
    reason: str
    estimated_cost: float
    fallback_plan: str = "local_fallback"


class HybridIntelligenceRouter:
    def __init__(self) -> None:
        self.policy_agent = policy_agent
        self.budget_guard = budget_guard
        self.local_client = RobustOllamaClient()
        self._openai_client: Optional[OpenAIClient] = None
        self._anthropic_client: Optional[AnthropicClient] = None

    @property
    def openai_client(self) -> Optional[OpenAIClient]:
        if self._openai_client is None:
            try:
                self._openai_client = OpenAIClient()
            except Exception as exc:
                logger.warning("OpenAI init failed: %s", exc)
                self._openai_client = None
        return self._openai_client

    @property
    def anthropic_client(self) -> Optional[AnthropicClient]:
        if self._anthropic_client is None:
            try:
                self._anthropic_client = AnthropicClient()
            except Exception as exc:
                logger.warning("Anthropic init failed: %s", exc)
                self._anthropic_client = None
        return self._anthropic_client

    async def route_task(self, task_type: str, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        context = context or {}
        try:
            decision = await self._make_routing_decision(task_type, prompt, context)
            logger.info("routing decision: %s", decision)
            if decision.use_cloud:
                budget = await self.budget_guard.check_budget(decision.estimated_cost)
                if not budget.get("approved"):
                    return await self._fallback_to_local(task_type, prompt, context, "budget")
            if decision.use_cloud:
                result = await self._call_cloud_ai(decision.provider, decision.model_name, prompt, context)
                await self.budget_guard.record_spending(decision.estimated_cost)
                return result
            return await self._call_local_ai(decision.model_name, prompt, context)
        except Exception as exc:
            logger.error("routing failed: %s", exc)
            return await self._fallback_to_local(task_type, prompt, context, str(exc))

    async def _make_routing_decision(self, task_type: str, prompt: str, context: Dict[str, Any]) -> RoutingDecision:
        complexity = self._assess_task_complexity(prompt, task_type, context)
        provider, model = self._select_provider_and_model(task_type, complexity)
        use_cloud = provider in {"openai", "anthropic"}
        est_cost = self._estimate_cost(provider, model, prompt) if use_cloud else 0.0
        return RoutingDecision(
            use_cloud=use_cloud,
            provider=provider,
            model_name=model,
            reason=f"task={task_type},complexity={complexity},provider={provider}",
            estimated_cost=est_cost,
        )

    def _assess_task_complexity(self, prompt: str, task_type: str, context: Dict[str, Any]) -> str:
        if "complexity" in context:
            return context["complexity"]
        if len(prompt) > 1200:
            return "high"
        low_words = ("fix", "update", "simple")
        if any(w in prompt.lower() for w in low_words):
            return "low"
        mid_words = ("implement", "create", "build", "test")
        if any(w in prompt.lower() for w in mid_words):
            return "medium"
        return "high"

    def _select_provider_and_model(self, task_type: str, complexity: str) -> Tuple[str, str]:
        # no cloud
        if not (self.openai_client or self.anthropic_client):
            return "local", self._select_local_model(task_type, complexity)
        # analysis → anthropic, else openai
        if task_type in ("research", "analysis", "planning", "architecture"):
            if self.anthropic_client:
                return "anthropic", "claude-3-sonnet-20240229"
            if self.openai_client:
                return "openai", "gpt-4"
        if task_type in ("coding", "debugging"):
            if self.openai_client:
                return "openai", "gpt-4"
            if self.anthropic_client:
                return "anthropic", "claude-3-sonnet-20240229"
        if complexity == "high":
            if self.openai_client:
                return "openai", "gpt-4"
            if self.anthropic_client:
                return "anthropic", "claude-3-sonnet-20240229"
        if self.openai_client:
            return "openai", "gpt-3.5-turbo"
        return "anthropic", "claude-3-haiku-20240307"

    def _select_local_model(self, task_type: str, complexity: str) -> str:
        models = self.policy_agent.routing_policy.local_models
        if complexity == "high" and "high_complexity" in models:
            return models["high_complexity"]
        return models.get("default", "llama2")

    def _estimate_cost(self, provider: str, model: str, prompt: str) -> float:
        if provider == "openai" and self.openai_client:
            return self.openai_client.estimate_cost(prompt, model)
        if provider == "anthropic" and self.anthropic_client:
            return self.anthropic_client.estimate_cost(prompt, model)
        return 0.01

    async def _call_cloud_ai(self, provider: str, model: str, prompt: str, context: Dict[str, Any]) -> str:
        if provider == "openai" and self.openai_client:
            return await self.openai_client.generate(prompt, model=model)
        if provider == "anthropic" and self.anthropic_client:
            return await self.anthropic_client.generate(prompt, model=model)
        raise ValueError(f"unsupported provider {provider}")

    async def _call_local_ai(self, model: str, prompt: str, context: Dict[str, Any]) -> str:
        result = await self.local_client.generate(model, prompt)
        return result.content

    async def _fallback_to_local(self, task_type: str, prompt: str, context: Dict[str, Any], reason: str) -> str:
        logger.warning("fallback to local due to %s", reason)
        model = self._select_local_model(task_type, "medium")
        return await self._call_local_ai(model, prompt, context)


hybrid_router = HybridIntelligenceRouter()
