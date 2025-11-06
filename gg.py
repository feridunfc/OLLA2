import sqlite3
conn = sqlite3.connect("data/ledger.db")
rows = conn.execute("SELECT id, sprint_id, manifest_hash FROM ledger_entries;").fetchall()
print(rows)
conn.close()
