import sqlite3
from pathlib import Path
from typing import Dict, Any
from .schema import Manifest
from ..config import settings
LEDGER = Path(settings.ledger_path)
def _ensure():
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(LEDGER) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS sprints(
            id TEXT PRIMARY KEY, goal TEXT, created_at TEXT DEFAULT (datetime('now')),
            pytest_ok INT, hash_ok INT, report_path TEXT);""")
        c.execute("""CREATE TABLE IF NOT EXISTS patch_ledger(
            id INTEGER PRIMARY KEY AUTOINCREMENT, sprint_id TEXT, artifact_id TEXT,
            mismatch_reason TEXT, risk_level TEXT, patch_applied INT,
            created_at TEXT DEFAULT (datetime('now')));""")
        c.commit()
def write_to_ledger(manifest: Manifest, status: Dict[str, Any], report_path: str = "workspace/report.md"):
    _ensure()
    with sqlite3.connect(LEDGER) as c:
        c.execute("BEGIN TRANSACTION")
        try:
            c.execute("INSERT OR REPLACE INTO sprints(id,goal,pytest_ok,hash_ok,report_path) VALUES (?,?,?,?,?)",
                      (manifest.sprint_id, manifest.sprint_purpose, int(status.get('pytest_ok',0)), int(status.get('hash_ok',0)), report_path))
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK"); raise
