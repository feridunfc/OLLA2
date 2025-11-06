# multiai/api/audit.py
import os, json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..core.audit_logger import audit_logger
from ..utils.pdf_reporter import pdf_reporter

router = APIRouter(prefix="/audit", tags=["audit"])

class ExportRequest(BaseModel):
    export_type: str = "json"   # json or csv
    include_pdf: bool = False

@router.post("/export")
async def export_audit(req: ExportRequest):
    try:
        os.makedirs("exports", exist_ok=True)
        export_id = audit_logger.export_audit_log(export_type=req.export_type)
        path = f"exports/{export_id}.{req.export_type}"
        result = {"export_id": export_id, "file": path}
        if req.include_pdf:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            pdf_buf = pdf_reporter.generate(export_id, data)
            pdf_path = f"exports/{export_id}.pdf"
            with open(pdf_path, "wb") as pf:
                pf.write(pdf_buf.getvalue())
            result["pdf"] = pdf_path
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
