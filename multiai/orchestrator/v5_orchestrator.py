import logging
from typing import Dict, Any
from ..agents.critic_agent import CriticAgent
from ..agents.patch_agent import PatchAgent
from ..core.auto_patch_executor import AutoPatchExecutor

logger = logging.getLogger(__name__)

class V5Orchestrator:
    """Critic → Patch → Test workflow orchestrator."""
    def __init__(self, sandbox_enabled: bool = False):
        self.critic = CriticAgent()
        self.patcher = PatchAgent()
        self.exec = AutoPatchExecutor(sandbox_enabled=sandbox_enabled, run_tests=False)

    async def run_critic_patch_flow(self, old_code: str, new_code: str, file_path: str="code.py") -> Dict[str, Any]:
        try:
            analysis = self.critic.analyze_diff(old_code, new_code)
            if analysis.get("status") != "success":
                return {"status": "error", "step": "critic", "error": "analysis failed"}
            patch = self.patcher.generate_patch(analysis, old_code, new_code, file_path)
            if patch.get("status") != "success":
                return {"status": "error", "step": "patch", "error": patch.get("error")}
            exec_result = await self.exec.apply_and_test_patch(patch["patch_file"])
            auto_ready = bool(exec_result.get("patch_safe"))
            return {"status": "success", "critic_analysis": analysis, "patch": patch, "execution": exec_result, "auto_patch_ready": auto_ready}
        except Exception as e:
            logger.exception("orchestrator failed")
            return {"status": "error", "error": str(e)}
