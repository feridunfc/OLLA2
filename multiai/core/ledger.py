# Sprint A — Append-only ledger
import sqlite3, time

def init_ledger(db_path='ledger.db'):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sprint TEXT,
        hash TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

def append_entry(sprint: str, manifest_hash: str):
    conn = sqlite3.connect('ledger.db')
    cur = conn.cursor()
    cur.execute('INSERT INTO ledger (sprint, hash, created_at) VALUES (?, ?, ?)',
                (sprint, manifest_hash, time.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
