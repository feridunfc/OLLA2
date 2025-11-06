-- migrations/001_init.sql
-- Initialize ledger database schema

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
);

CREATE TABLE IF NOT EXISTS manifest_hashes (
    sprint_id TEXT PRIMARY KEY,
    expected_sha256 TEXT NOT NULL,
    actual_sha256 TEXT NOT NULL,
    match_status BOOLEAN NOT NULL,
    validated_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ledger_sprint_id ON ledger_entries(sprint_id);
CREATE INDEX IF NOT EXISTS idx_ledger_timestamp ON ledger_entries(timestamp);
CREATE INDEX IF NOT EXISTS idx_ledger_hash ON ledger_entries(manifest_hash);

CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO migrations (name) VALUES ('001_init.sql');