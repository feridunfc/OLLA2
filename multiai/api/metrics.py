# Prometheus metrics endpoint
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, Counter

router = APIRouter()
calls = Counter('multiai_agent_calls_total', 'Agent calls', ['agent', 'status'])

@router.get('/metrics')
async def metrics():
    return Response(generate_latest(), media_type='text/plain')
