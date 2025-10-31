from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from ..core.hybrid_router import LLM
from ..agents.critic_agent import CriticAgent
from ..manifest.schema import Artifact
router = APIRouter(prefix="/api/critic", tags=["critic"])
class PatchRequest(BaseModel):
    artifact: Dict[str, Any]; actual_content: str; mismatch_reason: str
class PatchResponse(BaseModel):
    success: bool; analysis: Dict[str, Any]
@router.post("/patch", response_model=PatchResponse)
async def create_patch(req: PatchRequest):
    try:
        llm = LLM(); critic = CriticAgent(llm)
        art = Artifact(**req.artifact)
        analysis = await critic.analyze_mismatch(art, req.actual_content, req.mismatch_reason)
        return PatchResponse(success=True, analysis=analysis)
    except Exception as e:
        raise HTTPException(500, str(e))
