from typing import Dict, Any
from .base_olla2_agent import BaseOlla2Agent
from ..config.olla2_config import Olla2Config
from ..utils.structured_logging import get_logger

logger = get_logger(__name__)

class Olla2ResearcherAgent(BaseOlla2Agent):
    def __init__(self, config: Olla2Config | None = None):
        super().__init__("agents.research_agent", "ResearchAgent", config)

    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        topic = kwargs.get("topic") or (args[0] if args else "")
        depth = kwargs.get("depth", "medium")
        return await self.research_topic(topic, depth)

    async def research_topic(self, topic: str, depth: str = "medium") -> Dict[str, Any]:
        if self.olla2_ok and self.olla2_agent:
            try:
                result = self.olla2_agent.research_topic(topic, depth)
                return {"provider": "olla2", **result, "status": "success"}
            except Exception as e:
                logger.warning(f"OLLA2 research failed, fallback: {e}")
        # cloud fallback
        prompt = f"Research the topic: {topic}\nDepth: {depth}\nGive concise, referenced bullets."
        cloud = await self._fallback_cloud(prompt)
        return {"provider": cloud.get("provider"), "topic": topic, "depth": depth, "findings": cloud.get("result", ""), "sources": [], "status": "success"}
