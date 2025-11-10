class OllamaClient:
    """Mock Ollama client for testing and router integration."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def generate(self, prompt: str) -> str:
        """Fake async generation — used for test fallback."""
        return f"[mocked ollama response for prompt: {prompt[:40]}]"

    def __repr__(self):
        return f"<OllamaClient base_url={self.base_url}>"
