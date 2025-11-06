import os
import sqlite3

MIGRATIONS_DIR = "migrations"
DB_PATH = "data/ledger.db"

os.makedirs("data", exist_ok=True)

def get_applied_migrations(conn):
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
    except Exception:
        pass

    rows = conn.execute("SELECT name FROM migrations").fetchall()
    return {r[0] for r in rows}

def apply_migration(conn, name, path):
    print(f"Running migration: {name}")
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    try:
        conn.executescript(sql)
        conn.execute("INSERT INTO migrations (name) VALUES (?)", (name,))
        conn.commit()
        print(f"✅ Migration successful: {name}")
    except Exception as e:
        print(f"✗ Migration failed: {name} - {e}")

def main():
    conn = sqlite3.connect(DB_PATH)
    applied = get_applied_migrations(conn)

    for fname in sorted(os.listdir(MIGRATIONS_DIR)):
        if not fname.endswith(".sql"):
            continue
        if fname in applied:
            continue
        apply_migration(conn, fname, os.path.join(MIGRATIONS_DIR, fname))

    conn.close()

if __name__ == "__main__":
    main()
