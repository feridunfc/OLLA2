from ..core.hybrid_router import LLM
SUP_PROMPT = "Summarize sprint result as markdown. Input: {payload}"
class ASup:
    async def summarize(self, payload: dict, llm: LLM) -> str:
        return (await llm.complete(SUP_PROMPT.format(payload=payload))).strip()
