# multiai/core/ledger_signed.py
import json
import time
import sqlite3
import os
import logging
from typing import Dict, Any
from .deterministic_validator import validator
from .ledger_sign import ledger_signer


class SignedLedgerWriter:
    """Write signed manifest entries to ledger database"""

    def __init__(self, db_path: str = os.path.join("data", "ledger.db")):
        # ✅ DB'yi data klasörüne taşır
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

        # Klasör yoksa oluştur
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Tabloları garantiye al
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure ledger tables exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ledger_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    sprint_id TEXT NOT NULL,
                    manifest_hash TEXT NOT NULL,
                    manifest_data TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    public_key_fingerprint TEXT NOT NULL,
                    version TEXT DEFAULT 'v1',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS manifest_hashes (
                    sprint_id TEXT PRIMARY KEY,
                    expected_sha256 TEXT NOT NULL,
                    actual_sha256 TEXT NOT NULL,
                    match_status BOOLEAN NOT NULL,
                    validated_at REAL NOT NULL
                )
            """)
            conn.commit()

    async def write_manifest_to_ledger(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Insert signed manifest entry"""
        manifest_hash = validator.compute_manifest_hash(manifest)

        entry_data = {
            "timestamp": time.time(),
            "sprint_id": manifest.get("sprint_id", "unknown"),
            "manifest_hash": manifest_hash,
            "manifest_data": json.dumps(manifest),
            "version": "v1",
        }

        # Sign entry
        data_to_sign = json.dumps(entry_data, sort_keys=True)
        signature = ledger_signer.sign_data(data_to_sign)

        # Write to DB
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO ledger_entries 
                (timestamp, sprint_id, manifest_hash, manifest_data, signature, public_key_fingerprint)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry_data["timestamp"],
                entry_data["sprint_id"],
                entry_data["manifest_hash"],
                entry_data["manifest_data"],
                signature,
                ledger_signer.get_public_key_fingerprint()
            ))
            entry_id = cursor.lastrowid
            conn.commit()

        self.logger.info(f"✅ Written manifest to ledger: {entry_data['sprint_id']}")

        return {
            "ledger_id": entry_id,
            "sprint_id": entry_data["sprint_id"],
            "manifest_hash": manifest_hash,
            "signature": signature,
            "public_key_fingerprint": ledger_signer.get_public_key_fingerprint(),
            "timestamp": entry_data["timestamp"],
        }

    def verify_ledger_integrity(self, ledger_id: int) -> Dict[str, Any]:
        """Check if entry is intact and signature valid"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT timestamp, sprint_id, manifest_hash, manifest_data, signature
                FROM ledger_entries WHERE id = ?
            """, (ledger_id,)).fetchone()

            if not row:
                return {"valid": False, "error": "Entry not found"}

            timestamp, sprint_id, manifest_hash, manifest_data, signature = row
            entry_data = {
                "timestamp": timestamp,
                "sprint_id": sprint_id,
                "manifest_hash": manifest_hash,
                "manifest_data": manifest_data,
                "version": "v1",
            }

            data_to_verify = json.dumps(entry_data, sort_keys=True)
            is_valid = ledger_signer.verify_signature(data_to_verify, signature)

            return {
                "valid": is_valid,
                "sprint_id": sprint_id,
                "timestamp": timestamp,
                "manifest_hash": manifest_hash,
            }


# ✅ Global singleton instance
ledger_writer = SignedLedgerWriter()
