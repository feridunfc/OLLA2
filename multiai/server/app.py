import time, json, logging
from typing import Literal
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path
from ..core.hybrid_router import LLM
from ..manifest.schema import Manifest, ArtifactType
from ..manifest.repo import write_to_ledger
from ..core.deterministic_validator import validate_against_manifest
from ..agents.researcher import AResearch
from ..agents.architect import AArch
from ..agents.coder import ACoder
from ..agents.tester import ATest
from ..agents.debugger import ADebug
from ..agents.supervisor import ASup
from ..api.metrics import router as metrics_router, record_sprint_start, record_sprint_complete, record_agent_call
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("multiai")
app = FastAPI(title="MULTI-AI v4.8"); app.include_router(metrics_router)
class SprintRequest(BaseModel):
    goal: str; workdir: str = "workspace"; mode: Literal["local","cloud","auto"] = "auto"
async def run_sprint_background(req: SprintRequest, llm: LLM):
    work = Path(req.workdir); work.mkdir(parents=True, exist_ok=True)
    record_sprint_start(req.goal)
    status = {"pytest_ok": False, "hash_ok": False, "mismatches": [], "report_md": ""}
    try:
        t=time.time(); research = await AResearch().run(req.goal, llm); record_agent_call("researcher", True, time.time()-t)
        t=time.time(); mjson = await AArch().run(research, llm); record_agent_call("architect", True, time.time()-t)
        manifest = Manifest(**mjson); (work / f"{manifest.sprint_id}.json").write_text(json.dumps(mjson, indent=2), encoding="utf-8")
        outputs=[]; coder, tester, dbg = ACoder(), ATest(), ADebug()
        for art in manifest.artifacts:
            if art.type == ArtifactType.CODE:
                code = await coder.implement(artifact=art.model_dump(), directive=research, llm=llm)
                p = work / art.path; tester.write_file(p, code)
                ok, logs = await tester.run_pytest_async(work); status["pytest_ok"]=ok
                if not ok:
                    fixed = await dbg.fix_code(logs, code, llm); tester.write_file(p, fixed)
                    ok2, _ = await tester.run_pytest_async(work); status["pytest_ok"]=ok2
                outputs.append({"path": art.path, "status":"tested", "ok": status["pytest_ok"]})
            else:
                (work / art.path).parent.mkdir(parents=True, exist_ok=True)
                (work / art.path).write_text(f"# generated {art.type} {art.path}\n", encoding="utf-8")
                outputs.append({"path": art.path, "status":"generated"})
        ok, mismatches = validate_against_manifest(work, manifest); status["hash_ok"]=ok; status["mismatches"]=mismatches
        report = await ASup().summarize({"goal": req.goal, "outputs": outputs, "pytest_ok": status["pytest_ok"], "hash_ok": ok, "mismatches": mismatches}, llm)
        status["report_md"]=report; write_to_ledger(manifest, status); record_sprint_complete(req.goal, status["pytest_ok"] and status["hash_ok"])
        logger.info("Sprint finished.")
    except Exception as e:
        record_sprint_complete(req.goal, False); logger.exception("Sprint failed: %s", e)
@app.post("/api/sprint/start")
async def start_sprint_api(req: SprintRequest, background_tasks: BackgroundTasks):
    llm = LLM(); background_tasks.add_task(run_sprint_background, req, llm)
    return {"status":"started","goal":req.goal,"workdir":req.workdir}
