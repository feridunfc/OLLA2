# multiai/api/test_metrics.py
import random, time
from fastapi import APIRouter
from ..core.advanced_metrics import API_REQUESTS, LEDGER_WRITES, REQUEST_DURATION, ACTIVE_SPRINTS, BUDGET_USAGE

router = APIRouter(prefix="/test", tags=["test"])

@router.post("/alert")
async def trigger_alerts():
    # simulate errors and slow requests
    for _ in range(50):
        status = random.choice(["200", "500", "502"])
        API_REQUESTS.labels(method="GET", endpoint="/test/alert", status=status).inc()
    LEDGER_WRITES.labels(status="error").inc(5)
    BUDGET_USAGE.set(0.95)
    ACTIVE_SPRINTS.set(3)
    # simulate latency histogram
    REQUEST_DURATION.labels(endpoint="/test/alert").observe(2.5)
    return {"ok": True}
