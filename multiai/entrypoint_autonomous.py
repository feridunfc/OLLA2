from fastapi import FastAPI, Response
import uvicorn
import os
import logging
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY

from .core.enhanced_orchestrator import enhanced_orchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=\"OLLA2 Autonomous AI System\", version=\"6.0.0\")

@app.get(\"/healthz\")
async def health_check():
    \"\"\"Health check endpoint\"\"\"
    return {
        \"status\": \"healthy\", 
        \"service\": \"olla2-autonomous\",
        \"version\": \"6.0.0\",
        \"capabilities\": [\"self-orchestration\", \"autonomous-sprints\", \"learning-loop\"]
    }

@app.get(\"/metrics\")
async def metrics_endpoint():
    \"\"\"Prometheus metrics endpoint\"\"\"
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

@app.post(\"/api/sprint/autonomous\")
async def start_autonomous_sprint(sprint_data: dict):
    \"\"\"Start an autonomous AI sprint with self-orchestration\"\"\"
    try:
        sprint_goal = sprint_data.get(\"goal\", \"\")
        context = sprint_data.get(\"context\", {})
        
        if not sprint_goal:
            return {\"status\": \"error\", \"message\": \"Sprint goal required\"}
        
        result = await enhanced_orchestrator.execute_autonomous_sprint(sprint_goal, context)
        
        return {
            \"status\": \"success\",
            \"sprint_id\": f\"autonomous_{int(time.time())}\",
            \"result\": result
        }
        
    except Exception as e:
        logger.error(f\"Autonomous sprint failed: {e}\")
        return {\"status\": \"error\", \"message\": str(e)}

@app.get(\"/api/orchestration/patterns\")
async def get_learning_patterns():
    \"\"\"Get learned workflow patterns\"\"\"
    try:
        patterns = enhanced_orchestrator.self_orchestrator.workflow_patterns
        return {
            \"status\": \"success\",
            \"learned_patterns\": patterns,
            \"pattern_count\": len(patterns)
        }
    except Exception as e:
        return {\"status\": \"error\", \"message\": str(e)}

@app.get(\"/api/system/capabilities\")
async def get_system_capabilities():
    \"\"\"Get system capabilities and agent information\"\"\"
    capabilities = {
        \"system\": \"OLLA2 Autonomous AI Orchestration\",
        \"version\": \"6.0.0\", 
        \"agents\": list(enhanced_orchestrator.agent_registry.keys()),
        \"features\": [
            \"Self-orchestration\",
            \"Dynamic workflow optimization\", 
            \"Learning from feedback\",
            \"Performance auto-tuning\",
            \"Multi-agent coordination\"
        ],
        \"metrics\": \"Prometheus integration ready\"
    }
    return capabilities

import time
if __name__ == \"__main__\":
    port = int(os.getenv(\"PORT\", 8000))
    logger.info(f\"Starting OLLA2 Autonomous System on port {port}\")
    uvicorn.run(app, host=\"0.0.0.0\", port=port, log_level=\"info\")
