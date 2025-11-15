from fastapi import FastAPI, Response
import uvicorn
import os
import logging
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .github_app import router as github_router
from .core.enhanced_metrics import enhanced_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=\"OLLA2 Multi-AI System\", version=\"5.3.0\")

# Include routers
app.include_router(github_router, prefix=\"/api/github\")

@app.get(\"/healthz\")
async def health_check():
    \"\"\"Health check endpoint with metrics\"\"\"
    return {
        \"status\": \"healthy\", 
        \"service\": \"olla2\", 
        \"version\": \"5.3.0\",
        \"metrics\": \"enhanced\"
    }

@app.get(\"/metrics\")
async def metrics_endpoint():
    \"\"\"Prometheus metrics endpoint - returns proper format\"\"\"
    return Response(
        generate_latest(), 
        media_type=CONTENT_TYPE_LATEST
    )

@app.get(\"/api/metrics/agent-stats\")
async def agent_metrics():
    \"\"\"Custom agent metrics endpoint (JSON format)\"\"\"
    return {
        \"active_agents\": enhanced_metrics.agent_success_counts,
        \"success_rates\": {
            agent: (enhanced_metrics.agent_success_counts.get(agent, 0) / 
                   enhanced_metrics.agent_total_counts.get(agent, 1)) * 100
            for agent in set(list(enhanced_metrics.agent_success_counts.keys()) + 
                           list(enhanced_metrics.agent_total_counts.keys()))
        }
    }

@app.post(\"/api/sprint/start\")
async def start_sprint(sprint_data: dict):
    \"\"\"Start sprint with enhanced metrics\"\"\"
    try:
        # TODO: Integrate with actual orchestrator
        enhanced_metrics.record_sprint_completion(sprint_data)
        
        return {
            \"status\": \"success\", 
            \"sprint_id\": \"sprint_123\",
            \"metrics_recorded\": True
        }
    except Exception as e:
        logger.error(f\"Sprint start failed: {e}\")
        return {\"status\": \"error\", \"message\": str(e)}

if __name__ == \"__main__\":
    port = int(os.getenv(\"PORT\", 8000))
    logger.info(f\"Starting OLLA2 Enhanced Metrics server on port {port}\")
    uvicorn.run(app, host=\"0.0.0.0\", port=port, log_level=\"info\")
