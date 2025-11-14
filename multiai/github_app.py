from fastapi import APIRouter, Request
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def github_webhook(request: Request):
    try:
        payload = await request.json()
        event_type = request.headers.get("X-GitHub-Event", "unknown")
        
        logger.info(f"GitHub webhook received: {event_type}")
        
        if event_type == "pull_request" and payload.get("action") == "opened":
            return await handle_pr_opened(payload)
        else:
            return {"status": "ignored", "event_type": event_type}
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

async def handle_pr_opened(payload: dict):
    pr_number = payload["pull_request"]["number"]
    repo_name = payload["repository"]["full_name"]
    
    logger.info(f"Processing PR #{pr_number} in {repo_name}")
    
    # TODO: Mevcut orchestrator entegrasyonu
    return {
        "status": "processing", 
        "pr_number": pr_number,
        "repo": repo_name,
        "message": "PR review process started"
    }
