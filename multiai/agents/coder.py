from ..core.hybrid_router import LLM
CODER_PROMPT = "Implement artifact: {artifact}. Use research: {directive}. Return ONLY code."
class ACoder:
    async def implement(self, artifact: dict, directive: dict, llm: LLM) -> str:
        txt = await llm.complete(CODER_PROMPT.format(artifact=artifact, directive=directive))
        return txt.strip()
