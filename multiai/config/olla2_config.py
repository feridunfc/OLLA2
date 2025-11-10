from pydantic_settings import BaseSettings
from typing import Dict

class Olla2Config(BaseSettings):
    enabled: bool = True
    olla2_home: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: int = 30
    models: Dict[str, str] = {
        "coding": "codellama",
        "research": "llama2",
        "analysis": "llama2",
    }

    class Config:
        env_prefix = "OLLA2_"
        case_sensitive = False
