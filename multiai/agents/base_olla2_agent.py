import os, sys, importlib
from abc import ABC, abstractmethod
from typing import Any, Dict
from ..config.olla2_config import Olla2Config
from ..utils.structured_logging import get_logger

logger = get_logger(__name__)

class BaseOlla2Agent(ABC):
    def __init__(self, module_path: str, class_name: str, config: Olla2Config | None = None):
        self.cfg = config or Olla2Config()
        self.olla2_ok = False
        self.olla2_agent = None
        # attempt dynamic import strategies
        try:
            if self.cfg.olla2_home and self.cfg.olla2_home not in sys.path:
                sys.path.append(self.cfg.olla2_home)
            module = importlib.import_module(module_path)
            self.olla2_agent = getattr(module, class_name)()
            self.olla2_ok = True
            logger.info("OLLA2 component loaded", extra={"module": module_path, "class": class_name})
        except Exception as e:
            logger.warning(f"OLLA2 component unavailable: {module_path}.{class_name} -> {e}")

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        ...

    async def _fallback_cloud(self, prompt: str) -> Dict[str, Any]:
        # basic cloud LLM fallback; expected llm_router.complete returns dict with 'text' or 'content'
        from ..core.hybrid_router import llm_router  # rely on existing router in project
        try:
            resp = await llm_router.complete(prompt)
            text = resp.get("text") or resp.get("content") or ""
            return {"provider": "cloud", "result": text}
        except Exception as e:
            return {"provider": "cloud", "error": str(e), "result": ""}
