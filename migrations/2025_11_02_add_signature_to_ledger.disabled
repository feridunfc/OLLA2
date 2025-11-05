-- migrations/2025_11_02_add_signature_to_ledger.sql
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

ALTER TABLE ledger RENAME TO ledger_old;

CREATE TABLE ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint TEXT,
    manifest_id TEXT,
    manifest_hash TEXT,
    signature TEXT,
    public_key TEXT,
    signer_id TEXT,
    created_at TEXT
);

INSERT INTO ledger (id, sprint, manifest_hash, created_at)
SELECT id, sprint, hash, created_at FROM ledger_old;

DROP TABLE ledger_old;
COMMIT;
PRAGMA foreign_keys=ON;
