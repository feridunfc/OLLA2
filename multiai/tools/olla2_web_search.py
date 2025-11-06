from typing import Dict, Any
from ..utils.structured_logging import get_logger
from ..agents.base_olla2_agent import BaseOlla2Agent

logger = get_logger(__name__)

class Olla2WebSearch(BaseOlla2Agent):
    def __init__(self, config=None):
        super().__init__("tools.web_search", "WebSearchTool", config)

    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        query = kwargs.get("query") or (args[0] if args else "")
        max_results = kwargs.get("max_results", 5)
        return await self.search(query, max_results)

    async def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        if self.olla2_ok and self.olla2_agent:
            try:
                results = self.olla2_agent.search(query, max_results)
                return {"provider": "olla2", "query": query, "results": results, "total_results": len(results), "status": "success"}
            except Exception as e:
                logger.warning(f"OLLA2 web search failed, fallback: {e}")
        # fallback brief via cloud
        prompt = f"Provide a brief fact sheet for: {query}"
        cloud = await self._fallback_cloud(prompt)
        return {"provider": cloud.get("provider"), "query": query, "results": [{"title": query, "snippet": cloud.get("result", ""), "url": "local-knowledge"}], "total_results": 1, "status": "success"}
