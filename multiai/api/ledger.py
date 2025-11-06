# Ledger API endpoints
# multiai/api/ledger.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
from ..core.ledger_signed import ledger_writer
from ..core.deterministic_validator import validator

router = APIRouter(prefix="/ledger", tags=["ledger"])
logger = logging.getLogger(__name__)


class LedgerWriteRequest(BaseModel):
    sprint_id: str
    goal: str
    artifacts: List[str] = []
    budget_hint: Optional[float] = None
    tenant_id: Optional[str] = None


class LedgerWriteResponse(BaseModel):
    ledger_id: int
    sprint_id: str
    manifest_hash: str
    signature: str
    timestamp: float
    status: str = "success"


class LedgerVerifyResponse(BaseModel):
    valid: bool
    sprint_id: str
    ledger_id: int
    manifest_hash: str
    timestamp: float
    error: Optional[str] = None


@router.post("/write", response_model=LedgerWriteResponse)
async def write_ledger_entry(request: LedgerWriteRequest):
    """Write a new manifest to ledger"""
    try:
        manifest_data = {
            "sprint_id": request.sprint_id,
            "goal": request.goal,
            "artifacts": request.artifacts,
            "budget_hint": request.budget_hint,
            "tenant_id": request.tenant_id,
        }

        manifest = validator.create_sprint_manifest_with_hash(manifest_data)
        result = await ledger_writer.write_manifest_to_ledger(manifest)

        return LedgerWriteResponse(**result)

    except Exception as e:
        logger.error(f"Ledger write failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/{ledger_id}", response_model=LedgerVerifyResponse)
async def verify_ledger_entry(ledger_id: int):
    """Verify ledger entry integrity"""
    try:
        verification = ledger_writer.verify_ledger_integrity(ledger_id)

        if not verification["valid"]:
            return LedgerVerifyResponse(
                valid=False,
                sprint_id=verification.get("sprint_id", "unknown"),
                ledger_id=ledger_id,
                manifest_hash=verification.get("manifest_hash", ""),
                timestamp=verification.get("timestamp", 0),
                error=verification.get("error", "Verification failed"),
            )

        return LedgerVerifyResponse(
            valid=True,
            sprint_id=verification["sprint_id"],
            ledger_id=ledger_id,
            manifest_hash=verification["manifest_hash"],
            timestamp=verification["timestamp"],
        )

    except Exception as e:
        logger.error(f"Ledger verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entries")
async def get_ledger_entries(
    sprint_id: Optional[str] = Query(None),
    limit: int = Query(50, le=1000),
    offset: int = Query(0),
):
    """List ledger entries"""
    import sqlite3
    DB_PATH = "data/ledger.db"

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        query = "SELECT id, timestamp, sprint_id, manifest_hash, signature FROM ledger_entries"
        params = []

        if sprint_id:
            query += " WHERE sprint_id = ?"
            params.append(sprint_id)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return {
            "entries": [
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "sprint_id": row[2],
                    "manifest_hash": row[3],
                    "signature": row[4],
                }
                for row in rows
            ],
            "total": len(rows),
        }

    except Exception as e:
        import logging
        logging.error(f"Failed to fetch ledger entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter
import sqlite3

# router = APIRouter()

DB_PATH = "data/ledger.db"

@router.get("/ledger/list")
def list_ledger():
    """List all ledger entries"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, sprint_id, hash, signature, timestamp FROM ledger ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "ledger_id": r[0],
            "sprint_id": r[1],
            "manifest_hash": r[2],
            "signature": r[3],
            "timestamp": r[4],
        }
        for r in rows
    ]
