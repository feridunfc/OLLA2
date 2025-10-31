from ..core.hybrid_router import LLM
DEBUG_PROMPT = "Tests failed. Logs: {logs}. Fix this Python code:\n{code}\nReturn ONLY corrected code."
class ADebug:
    async def fix_code(self, logs: str, code: str, llm: LLM) -> str:
        txt = await llm.complete(DEBUG_PROMPT.format(logs=logs, code=code))
        return txt.strip()
