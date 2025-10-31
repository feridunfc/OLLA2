from ..core.hybrid_router import LLM
ARCH_PROMPT = "Given research JSON: {research}. Produce Manifest JSON with fields sprint_id,sprint_purpose,artifacts[]."
class AArch:
    async def run(self, research: dict, llm: LLM) -> dict:
        txt = await llm.complete(ARCH_PROMPT.format(research=research), json_mode=True)
        data = llm.safe_json(txt, {})
        if not data: data = {"sprint_id":"sprint-fallback","sprint_purpose":"fallback","artifacts":[]}
        return data
