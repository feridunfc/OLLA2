# multiai/core/ledger_signed.py
import sqlite3, json, hashlib, datetime
from pathlib import Path
from .ledger_sign import sign_manifest, load_public_pem, load_private_pem

LEDGER_PATH = Path("ledger.db")

def get_conn(path: Path = LEDGER_PATH):
    conn = sqlite3.connect(str(path), timeout=30, isolation_level=None, check_same_thread=False)
    # WAL + biraz performans
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def write_manifest_to_ledger(manifest: dict, signer_id: str = "system"):
    """Manifest'i imzalayıp ledger tablosuna ekler."""
    conn = get_conn()
    try:
        manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
        manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
        signature_b64 = sign_manifest(manifest_bytes)
        public_pem = load_public_pem().decode("utf-8")

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ledger (sprint, manifest_id, manifest_hash, signature, public_key, signer_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                manifest.get("sprint") or manifest.get("sprint_id") or "",
                manifest.get("id") or manifest.get("manifest_id") or "",
                manifest_hash,
                signature_b64,
                public_pem,
                signer_id,
                datetime.datetime.now(datetime.UTC).isoformat(),
            ),
        )
        return manifest_hash, signature_b64
    finally:
        conn.close()
