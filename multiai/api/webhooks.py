# multiai/api/webhooks.py
from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
import logging, os
from typing import Optional
from ..core.ledger_signed import ledger_writer

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


class LedgerWebhookRequest(BaseModel):
    ledger_id: int
    sprint_id: str
    action: str = "webhook_verify"


class WebhookResponse(BaseModel):
    status: str
    ledger_id: int
    sprint_id: str
    valid: Optional[bool] = None
    error: Optional[str] = None
    manifest_hash: Optional[str] = None
    timestamp: Optional[float] = None


@router.post("/ledger-event", response_model=WebhookResponse)
async def handle_ledger_webhook(
    request: LedgerWebhookRequest,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None)
):
    """Handle ledger webhook from n8n"""
    if not await _verify_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # Background verification
        background_tasks.add_task(
            _process_ledger_verification,
            request.ledger_id,
            request.sprint_id,
        )

        return WebhookResponse(
            status="processing",
            ledger_id=request.ledger_id,
            sprint_id=request.sprint_id,
        )

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return WebhookResponse(
            status="error",
            ledger_id=request.ledger_id,
            sprint_id=request.sprint_id,
            error=str(e),
        )


async def _process_ledger_verification(ledger_id: int, sprint_id: str):
    """Background verification task"""
    try:
        verification = ledger_writer.verify_ledger_integrity(ledger_id)
        logger.info(f"Ledger verification completed: {verification}")
    except Exception as e:
        logger.error(f"Background verification failed: {e}")


async def _verify_api_key(api_key: str) -> bool:
    """Validate n8n API key"""
    expected_key = os.getenv("N8N_API_KEY", "dev-key")
    return api_key == expected_key
