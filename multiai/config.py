from pydantic import BaseModel
import os, pathlib
class Settings(BaseModel):
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    ledger_path: str = os.getenv("LEDGER_DB", str(pathlib.Path("data/ledger.sqlite")))
settings = Settings()
