# scripts/run_migrations.py
import sqlite3
import sys
from pathlib import Path

def run_migrations():
    migrations_dir = Path("migrations")
    db_path = "ledger.db"

    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        applied = {row[0] for row in conn.execute("SELECT name FROM migrations")}
        for migration_file in sorted(migrations_dir.glob("*.sql")):
            if migration_file.name not in applied:
                print(f"Running migration: {migration_file.name}")
                with open(migration_file, 'r', encoding='utf-8') as f:
                    sql = f.read()
                try:
                    conn.executescript(sql)
                    print(f"\u2713 Migration successful: {migration_file.name}")
                except Exception as e:
                    print(f"\u2717 Migration failed: {migration_file.name} - {e}")
                    sys.exit(1)

if __name__ == "__main__":
    run_migrations()