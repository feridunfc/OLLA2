import asyncio
from typing import Dict, Any
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.structured_logging import get_logger, log_operation
from ..config.olla2_config import Olla2Config
from ..agents.olla2_coder import Olla2CoderAgent
from ..agents.olla2_researcher import Olla2ResearcherAgent
from ..tools.olla2_web_search import Olla2WebSearch
from ..models.ollama_client import OllamaClient  # assumes present in repo

logger = get_logger(__name__)

class EnhancedLLMRouter:
    def __init__(self, config: Olla2Config | None = None):
        self.cfg = config or Olla2Config()
        self.cb = CircuitBreaker(failure_threshold=3, timeout_seconds=30)
        self._init_agents()
        self.ollama = OllamaClient(base_url=self.cfg.ollama_base_url)

    def _init_agents(self):
        self.agents = {
            "code_generation": Olla2CoderAgent(self.cfg),
            "research": Olla2ResearcherAgent(self.cfg),
            "web_search": Olla2WebSearch(self.cfg),
        }

    async def health(self) -> Dict[str, Any]:
        checks = {
            "olla2_enabled": self.cfg.enabled,
            "ollama_base_url": self.cfg.ollama_base_url,
        }
        # cheap ping to /api/tags could be added here
        return {"ok": True, "checks": checks}

    async def route_task(self, task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        agent = self.agents.get(task_type)
        if not agent:
            return {"status": "error", "reason": f"Unknown task_type {task_type}"}

        async def _exec():
            if task_type == "code_generation":
                return await agent.generate_code(data.get("requirements", ""), data.get("context", {}))
            if task_type == "research":
                return await agent.research_topic(data.get("topic", ""), data.get("depth", "medium"))
            if task_type == "web_search":
                return await agent.search(data.get("query", ""), data.get("max_results", 5))
            return {"status": "error", "reason": "unhandled task"}

        result = await self.cb.run(_exec)
        log_operation(logger, "route_task", {"task_type": task_type, "provider": result.get("provider")})
        return {"status": "success", **result}

# global (optional) instance
enhanced_llm_router = EnhancedLLMRouter()
