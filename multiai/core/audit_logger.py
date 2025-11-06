# multiai/core/audit_logger.py
import os
import json
import csv
import sqlite3
import base64
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class AuditLogger:
    def __init__(self, db_path: str = "audit.db"):
        self.db_path = db_path
        self._ensure_tables()
        self._setup_encryption()

    def _ensure_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    sprint_id TEXT,
                    agent_type TEXT,
                    action TEXT NOT NULL,
                    resource TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    status TEXT,
                    error_message TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_exports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    export_id TEXT UNIQUE NOT NULL,
                    export_type TEXT NOT NULL,
                    date_range_start DATETIME,
                    date_range_end DATETIME,
                    filters TEXT,
                    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    generated_by TEXT,
                    file_path TEXT,
                    checksum TEXT,
                    signature TEXT
                )
                """
            )
            conn.commit()

    def _setup_encryption(self):
        key = os.getenv('AUDIT_ENCRYPTION_KEY')
        if key:
            k = base64.urlsafe_b64encode(key.encode()[:32].ljust(32, b'\0'))
            self.cipher = Fernet(k)
        else:
            self.cipher = None

    def _contains_sensitive_data(self, details: Dict[str, Any]) -> bool:
        sensitive = ['password', 'token', 'key', 'secret', 'private']
        s = json.dumps(details).lower()
        return any(x in s for x in sensitive)

    def log_event(self, event_type: str, action: str, details: Dict[str, Any],
                  user_id: Optional[str] = None, sprint_id: Optional[str] = None,
                  agent_type: Optional[str] = None, resource: Optional[str] = None,
                  ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        try:
            details_json = json.dumps(details)
            if self.cipher and self._contains_sensitive_data(details):
                details_json = self.cipher.encrypt(details_json.encode()).decode()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO audit_events
                    (event_type, user_id, sprint_id, agent_type, action, resource, details, ip_address, user_agent, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (event_type, user_id, sprint_id, agent_type, action, resource, details_json, ip_address, user_agent, "success")
                )
                conn.commit()
            logger.info("Audit event logged: %s - %s", event_type, action)
        except Exception as e:
            logger.error("Failed to log audit event: %s", e)

    def _get_events_for_export(self, date_range: Optional[tuple], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        q = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        if date_range:
            q += " AND timestamp BETWEEN ? AND ?"
            params.extend(date_range)
        if filters:
            for k, v in filters.items():
                q += f" AND {k} = ?"
                params.append(v)
        q += " ORDER BY timestamp DESC"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(q, params)
            return [dict(r) for r in cur.fetchall()]

    def _export_json(self, export_id: str, events: List[Dict[str, Any]]) -> str:
        os.makedirs("exports", exist_ok=True)
        path = f"exports/{export_id}.json"
        data = {"export_id": export_id, "generated_at": datetime.now().isoformat(), "event_count": len(events), "events": events}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return path

    def _export_csv(self, export_id: str, events: List[Dict[str, Any]]) -> str:
        os.makedirs("exports", exist_ok=True)
        path = f"exports/{export_id}.csv"
        if not events:
            headers = ['id', 'timestamp', 'event_type', 'action', 'user_id', 'sprint_id']
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=headers)
                w.writeheader()
            return path
        headers = list(events[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            w.writerows(events)
        return path

    def _record_export(self, export_id: str, export_type: str, date_range: Optional[tuple], filters: Optional[Dict[str, Any]], file_path: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO data_exports (export_id, export_type, date_range_start, date_range_end, filters, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (export_id, export_type, date_range[0] if date_range else None, date_range[1] if date_range else None, json.dumps(filters) if filters else None, file_path)
            )
            conn.commit()

    def export_audit_log(self, export_type: str = 'json', date_range: Optional[tuple] = None, filters: Optional[Dict[str, Any]] = None) -> str:
        export_id = f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        events = self._get_events_for_export(date_range, filters)
        if export_type == 'json':
            path = self._export_json(export_id, events)
        elif export_type == 'csv':
            path = self._export_csv(export_id, events)
        else:
            raise ValueError("Unsupported export type")
        self._record_export(export_id, export_type, date_range, filters, path)
        return export_id

audit_logger = AuditLogger()
