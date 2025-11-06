from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from ..core.enhanced_llm_router import enhanced_llm_router

router = APIRouter()

class CodeReq(BaseModel):
    requirements: str = Field(..., min_length=5)
    context: Optional[Dict[str, Any]] = None

class ResearchReq(BaseModel):
    topic: str = Field(..., min_length=3)
    depth: str = Field(default="medium")

class SearchReq(BaseModel):
    query: str = Field(..., min_length=2)
    max_results: int = Field(default=5, ge=1, le=25)

@router.get("/health")
async def health():
    return await enhanced_llm_router.health()

@router.post("/code")
async def generate_code(req: CodeReq):
    try:
        return await enhanced_llm_router.route_task("code_generation", req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/research")
async def research(req: ResearchReq):
    try:
        return await enhanced_llm_router.route_task("research", req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/web_search")
async def web_search(req: SearchReq):
    try:
        return await enhanced_llm_router.route_task("web_search", req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
