from typing import Dict, Any
from .base_olla2_agent import BaseOlla2Agent
from ..config.olla2_config import Olla2Config
from ..utils.structured_logging import get_logger
from ..models.ollama_client import OllamaClient  # assume exists in your repo

logger = get_logger(__name__)

class Olla2CoderAgent(BaseOlla2Agent):
    def __init__(self, config: Olla2Config | None = None):
        super().__init__("agents.coding_agent", "CodingAgent", config)
        self.client = OllamaClient(base_url=(config.ollama_base_url if config else "http://localhost:11434"))
        self.model = (config.models.get("coding") if config else "codellama")

    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        req = kwargs.get("requirements") or (args[0] if args else "")
        ctx: Dict[str, Any] = kwargs.get("context") or {}
        return await self.generate_code(req, ctx)

    def _build_prompt(self, requirements: str, context: Dict[str, Any]) -> str:
        language = context.get("language", "python")
        framework = context.get("framework", "")
        patterns = ", ".join(context.get("patterns", []))
        return f"""
You are an expert {language} developer. Generate production-ready code.

REQUIREMENTS:
{requirements}

CONTEXT:
- Language: {language}
- Framework: {framework}
- Patterns: {patterns}
- Quality: High (production standards)

CONSTRAINTS:
- Proper error handling
- Type annotations
- Docstrings
- Testable design

Return ONLY the code without explanations.
"""

    async def generate_code(self, requirements: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}
        # Primary: OLLA2 CodingAgent if available
        if self.olla2_ok and self.olla2_agent:
            try:
                res = self.olla2_agent.generate_code(requirements, context)  # sync in OLLA2
                return {"provider": "olla2", **res}
            except Exception as e:
                logger.warning(f"OLLA2 coder failed, falling back: {e}")

        # Secondary: local Ollama
        try:
            prompt = self._build_prompt(requirements, context)
            res = self.client.generate(self.model, prompt)
            return {"provider": "ollama", "code": res.get("response", ""), "context": context}
        except Exception as e:
            logger.warning(f"Ollama failed, falling back to cloud: {e}")

        # Final: cloud LLM
        prompt = self._build_prompt(requirements, context)
        cloud = await self._fallback_cloud(prompt)
        return {"provider": cloud.get("provider"), "code": cloud.get("result", ""), "context": context}
