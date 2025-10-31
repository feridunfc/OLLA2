"""
Manifest doğrulama aracı.
Ledger'daki hash ile dosyanın mevcut hash'ini karşılaştırır.
"""

import sqlite3
import sys
from multiai.core.ledger_signed import compute_hash

def verify(manifest_id):
    conn = sqlite3.connect("ledger.db")
    cursor = conn.execute("SELECT hash FROM ledger WHERE manifest_id=?", (manifest_id,))
    row = cursor.fetchone()
    if not row:
        print(f"[!] Manifest ID bulunamadı: {manifest_id}")
        return False

    expected_hash = row[0]
    file_path = f"manifests/{manifest_id}.json"
    current_hash = compute_hash(file_path)

    if current_hash == expected_hash:
        print(f"[✔] Doğrulama başarılı: {manifest_id}")
        return True
    else:
        print(f"[❌] Doğrulama hatası: {manifest_id}")
        print(f"Beklenen: {expected_hash}\nBulunan : {current_hash}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python scripts/verify_manifest.py <manifest_id>")
        sys.exit(1)
    verify(sys.argv[1])
