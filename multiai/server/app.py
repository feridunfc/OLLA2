# multiai/server/app.py
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException

from multiai.api import ledger, webhooks, metrics
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MULTIAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI(title="MULTIAI API")

# 🔹 Router’ları ekle
app.include_router(ledger.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(metrics.router)

# 🔹 YENİ V5 importları (fallback'lı)
try:
    from ..schema.enhanced_manifest import SprintManifest, ArtifactType
except Exception:
    class SprintManifest:
        def __init__(self, sprint_id: str, goal: str, budget_hint=None, tenant_id=None):
            self.sprint_id = sprint_id
            self.goal = goal
            self.budget_hint = budget_hint
            self.tenant_id = tenant_id
    ArtifactType = None

try:
    from ..core.ledger_signed import write_manifest_to_ledger, verify_ledger_integrity
except Exception:
    async def write_manifest_to_ledger(manifest: SprintManifest):
        return {"hash": "dryrun-ledger-hash"}
    async def verify_ledger_integrity():
        return True

try:
    from ..core.hybrid_router import llm_router
except Exception:
    class DummyLLM:
        async def complete(self, *a, **kw):
            return {"ok": True, "cost": 0.0, "text": "dryrun"}
    llm_router = DummyLLM()

try:
    from ..utils.secure_sandbox import sandbox_runner
except Exception:
    sandbox_runner = None


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/api/sprint/start")
async def start_sprint(sprint_data: Dict[str, Any]):
    try:
        manifest = SprintManifest(
            sprint_id=sprint_data['sprint_id'],
            goal=sprint_data['goal'],
            budget_hint=sprint_data.get('budget_hint'),
            tenant_id=sprint_data.get('tenant_id')
        )
        ledger_entry = await write_manifest_to_ledger(manifest)
        analysis = await llm_router.complete(
            f"Analyze sprint goal: {sprint_data['goal']}",
            json_mode=True
        )
        return {
            "status": "started",
            "ledger_hash": ledger_entry.get('hash', ''),
            "analysis": analysis
        }
    except Exception as e:
        logging.error(f"Sprint start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
