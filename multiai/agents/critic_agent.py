import hashlib, logging
from ..core.hybrid_router import LLM
log = logging.getLogger("critic")
CRITIC_PROMPT = '''You are a Code Critic. Given expected hash, actual hash and file path, produce JSON:
{"analysis":"...", "risk_level":"low|medium|high", "patch_content":"", "suggested_fix":"..."}
Context: expected={expected}, actual={actual}, path={path}, reason={reason}, content={content}
Return ONLY JSON.'''
class CriticAgent:
    def __init__(self, llm: LLM): self.llm = llm
    async def analyze_mismatch(self, artifact, actual_content: str, mismatch_reason: str) -> dict:
        expected = artifact.sha256; actual = hashlib.sha256(actual_content.encode()).hexdigest()
        txt = await self.llm.complete(CRITIC_PROMPT.format(expected=expected, actual=actual, path=artifact.path, reason=mismatch_reason, content=actual_content), json_mode=True)
        return self.llm.safe_json(txt, {"analysis":"n/a","risk_level":"high","patch_content":"","suggested_fix":"manual"})
