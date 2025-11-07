import sqlite3, json, hashlib, logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger("deterministic_ledger")

class DeterministicLedger:
    def __init__(self, db_path: str = "sprint_ledger.db"):
        self.db_path = Path(db_path)
        self._init_database()

    def _init_database(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sprint_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sprint_id TEXT NOT NULL,
                    manifest_hash TEXT NOT NULL,
                    digital_signature TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'system',
                    status TEXT DEFAULT 'created',
                    UNIQUE(sprint_id, manifest_hash)
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artifact_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sprint_id TEXT NOT NULL,
                    artifact_id TEXT NOT NULL,
                    expected_hash TEXT NOT NULL,
                    actual_hash TEXT,
                    status TEXT DEFAULT 'pending',
                    validated_at TIMESTAMP,
                    validation_result TEXT,
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(sprint_id, artifact_id)
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    previous_hash TEXT,
                    new_hash TEXT,
                    performed_by TEXT DEFAULT 'system',
                    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    signature TEXT
                )""")
            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=30, isolation_level=None, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
        finally:
            conn.close()

    def record_sprint_manifest(self, sprint_id: str, manifest_hash: str, signature: Optional[str], created_by: str) -> str:
        with self._get_connection() as conn:
            cur = conn.execute("""
                INSERT OR IGNORE INTO sprint_ledger (sprint_id, manifest_hash, digital_signature, created_by)
                VALUES (?, ?, ?, ?)
            """, (sprint_id, manifest_hash, signature, created_by))
            if cur.rowcount == 0:
                raise sqlite3.IntegrityError("Duplicate sprint_id + manifest_hash")
            ledger_id = cur.lastrowid
            conn.execute("""
                INSERT INTO audit_trail (operation, entity_type, entity_id, new_hash, performed_by)
                VALUES (?, ?, ?, ?, ?)
            """, ("CREATE", "sprint_manifest", sprint_id, manifest_hash, created_by))
            conn.commit()
            return str(ledger_id)

    def update_artifact_hash(self, sprint_id: str, artifact_id: str, actual_hash: Optional[str], validation_result: str):
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE artifact_ledger
                SET actual_hash = ?, status = ?, validated_at = CURRENT_TIMESTAMP, validation_result = ?
                WHERE sprint_id = ? AND artifact_id = ?
            """, (actual_hash, validation_result, validation_result, sprint_id, artifact_id))
            conn.execute("""
                INSERT INTO audit_trail (operation, entity_type, entity_id, new_hash, performed_by)
                VALUES (?, ?, ?, ?, ?)
            """, ("UPDATE", "artifact", f"{sprint_id}:{artifact_id}", actual_hash or "error", "system"))
            conn.commit()

    def validate_sprint_artifacts(self, sprint_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cur = conn.execute("""
                SELECT artifact_id, expected_hash, actual_hash, status, file_path
                FROM artifact_ledger WHERE sprint_id = ?
            """, (sprint_id,))
            rows = cur.fetchall()
            results = {"sprint_id": sprint_id, "total_artifacts": len(rows), "validated_artifacts": 0,
                       "mismatched_artifacts": 0, "pending_artifacts": 0, "details": []}
            for aid, exp, act, st, fp in rows:
                if act is None:
                    results["pending_artifacts"] += 1
                    results["details"].append({"artifact_id": aid, "status": "pending", "file_path": fp})
                elif act == exp:
                    results["validated_artifacts"] += 1
                    results["details"].append({"artifact_id": aid, "status": "validated", "file_path": fp})
                else:
                    results["mismatched_artifacts"] += 1
                    results["details"].append({"artifact_id": aid, "status": "mismatch",
                                               "expected_hash": exp, "actual_hash": act, "file_path": fp})
            if results["mismatched_artifacts"] == 0:
                conn.execute("UPDATE sprint_ledger SET status = ? WHERE sprint_id = ?", ("validated", sprint_id))
            else:
                conn.execute("UPDATE sprint_ledger SET status = ? WHERE sprint_id = ?", ("hash_mismatch", sprint_id))
            conn.commit()
            return results

    def get_sprint_audit_trail(self, sprint_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute("""
                SELECT operation, entity_type, entity_id, previous_hash, new_hash, performed_by, performed_at, signature
                FROM audit_trail WHERE entity_id = ? OR entity_id LIKE ?
                ORDER BY performed_at
            """, (sprint_id, f"{sprint_id}:%"))
            return [{"operation": r[0], "entity_type": r[1], "entity_id": r[2], "previous_hash": r[3],
                     "new_hash": r[4], "performed_by": r[5], "performed_at": r[6], "signature": r[7]}
                    for r in cur.fetchall()]

    def verify_sprint_integrity(self, sprint_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cur = conn.execute("""
                SELECT manifest_hash, digital_signature, status FROM sprint_ledger WHERE sprint_id = ?
            """, (sprint_id,))
            row = cur.fetchone()
            if not row:
                return {"valid": False, "error": "Sprint not found"}
            mhash, dsig, st = row
            cur = conn.execute("""
                SELECT COUNT(*) as total, COUNT(CASE WHEN actual_hash = expected_hash THEN 1 END) as matched,
                       COUNT(CASE WHEN actual_hash != expected_hash THEN 1 END) as mismatched,
                       COUNT(CASE WHEN actual_hash IS NULL THEN 1 END) as pending
                FROM artifact_ledger WHERE sprint_id = ?
            """, (sprint_id,))
            stats = cur.fetchone()
            audit_entries = self.get_sprint_audit_trail(sprint_id)
            return {"valid": True, "sprint_id": sprint_id, "manifest_hash": mhash,
                    "digital_signature": dsig is not None, "status": st,
                    "artifacts": {"total": stats[0], "matched": stats[1], "mismatched": stats[2], "pending": stats[3]},
                    "audit_entries": len(audit_entries),
                    "integrity_check": "passed" if stats[2] == 0 else "failed"}
