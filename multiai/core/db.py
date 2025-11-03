# multiai/core/db.py
import sqlite3

def get_sqlite(path: str = "ledger.db"):
    conn = sqlite3.connect(path, timeout=30, isolation_level=None, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn
