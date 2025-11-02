"""
Ledger & Determinism — v4.9
Kurumsal izlenebilirlik ve tekrarlanabilirlik için imzalı manifest ledger'ı.
"""

import hashlib
import sqlite3
import datetime
import subprocess
import os
from pathlib import Path


LEDGER_PATH = Path("ledger.db")


def compute_hash(file_path: str) -> str:
    """Dosyanın SHA256 hash'ini üret."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def sign_hash(hash_value: str) -> str:
    """Test ortamı için sahte imza üretir."""
    return f"FAKE_SIGNATURE::{hash_value[:12]}"



def init_ledger():
    """Ledger veritabanını oluştur (yoksa)."""
    conn = sqlite3.connect(LEDGER_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manifest_id TEXT,
            sprint TEXT,
            hash TEXT,
            signature TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def write_to_ledger(manifest_id: str, sprint: str, manifest_path: str):
    """Manifest dosyasını hashle, imzala ve ledger’a yaz."""
    init_ledger()
    hash_value = compute_hash(manifest_path)
    signature = sign_hash(hash_value)

    conn = sqlite3.connect(LEDGER_PATH)
    conn.execute(
        "INSERT INTO ledger (manifest_id, sprint, hash, signature, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            manifest_id,
            sprint,
            hash_value,
            signature,
            datetime.datetime.now(datetime.UTC).isoformat(),
        ),
    )
    conn.commit()
    conn.close()

    print(f"[✔] Ledger’a eklendi: {manifest_id} | {sprint}")
    return hash_value


def verify_manifest(manifest_path: str, expected_hash: str) -> bool:
    """Manifest dosyasının hash’ini kontrol et."""
    current_hash = compute_hash(manifest_path)
    return current_hash == expected_hash


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ledger & Determinism CLI")
    parser.add_argument("--manifest", required=True, help="Manifest dosya yolu")
    parser.add_argument("--sprint", required=True, help="Sprint adı")
    parser.add_argument("--id", required=True, help="Manifest ID")
    args = parser.parse_args()

    write_to_ledger(args.id, args.sprint, args.manifest)
