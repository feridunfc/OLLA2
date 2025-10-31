from types import SimpleNamespace
import httpx, logging
from tenacity import retry, stop_after_attempt, wait_exponential
from pybreaker import CircuitBreaker
from ..config import settings
log = logging.getLogger("ollama")
class RobustOllamaClient:
    def __init__(self, base_url: str | None = None, timeout: int = 60, max_retries: int = 3):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=50),
            headers={"User-Agent": "multiai-v4.8"}
        )
        self.breaker = CircuitBreaker(fail_max=5, reset_timeout=60)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def generate(self, model: str, prompt: str) -> SimpleNamespace:
        body = {"model": model, "prompt": prompt, "stream": False}
        url = f"{self.base_url}/api/generate"
        with self.breaker:
            r = await self.client.post(url, json=body)
            r.raise_for_status()
            js = r.json()
            text = js.get("response") or js.get("text") or ""
            return SimpleNamespace(success=True, content=text)
