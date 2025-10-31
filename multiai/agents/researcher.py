from ..core.hybrid_router import LLM
RESEARCH_PROMPT = "Analyze the goal: {goal}. Return JSON with tech_stack, requirements, risks, acceptance_criteria."
class AResearch:
    async def run(self, goal: str, llm: LLM) -> dict:
        txt = await llm.complete(RESEARCH_PROMPT.format(goal=goal), json_mode=True)
        return llm.safe_json(txt, {"tech_stack": [], "requirements": [], "risks": [], "acceptance_criteria": []})
