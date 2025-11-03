import time
from fastapi import APIRouter, Request, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
router = APIRouter()
agent_calls = Counter("multiai_agent_calls_total","Total agent calls",["agent","outcome"])
current_budget = Gauge("multiai_budget_usage","Current budget usage")
agent_latency = Histogram("multiai_agent_latency_seconds","Latency seconds",["agent"])
@router.get("/metrics")
def metrics(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
async def metrics_middleware(request:Request, call_next):
    s=time.time(); resp=await call_next(request); agent_latency.labels(agent="api").observe(time.time()-s); return resp
