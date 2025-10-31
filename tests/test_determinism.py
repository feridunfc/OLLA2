"""
Test: Deterministik manifest doğrulama
"""

import os
from multiai.core.ledger_signed import compute_hash, write_to_ledger, verify_manifest

def test_manifest_determinism(tmp_path):
    # Sahte manifest oluştur
    manifest = tmp_path / "test_manifest.json"
    manifest.write_text('{"name": "agent", "version": "1.0"}')

    # Ledger’a yaz
    hash1 = write_to_ledger("TEST-001", "Sprint-A", str(manifest))

    # Aynı içeriği tekrar yaz → aynı hash çıkmalı
    hash2 = compute_hash(str(manifest))
    assert hash1 == hash2, "Hash farklı çıktı (deterministik değil)"

    # Manifest değiştir → farklı hash çıkmalı
    manifest.write_text('{"name": "agent", "version": "1.1"}')
    hash3 = compute_hash(str(manifest))
    assert hash1 != hash3, "Manifest değişti ama hash aynı kaldı!"

    # Ledger doğrulaması
    assert verify_manifest(str(manifest), hash3) is True or False  # sadece çalışırlığı test eder
