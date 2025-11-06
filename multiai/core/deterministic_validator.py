# multiai/core/deterministic_validator.py
import hashlib
import json
from typing import Dict, Any
from pathlib import Path
import logging

class DeterministicValidator:
    """Manifest hash calculation and validation"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def compute_manifest_hash(self, manifest_data: Dict[str, Any]) -> str:
        """Compute SHA-256 hash ignoring meta fields like version, hash_algorithm, expected_sha256."""
        clean_data = {
            k: v
            for k, v in manifest_data.items()
            if k not in ("expected_sha256", "version", "hash_algorithm")
        }
        serialized = json.dumps(clean_data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def validate_manifest_integrity(self, expected_sha256: str, actual_manifest: Dict[str, Any]) -> Dict[str, Any]:
        actual_sha256 = self.compute_manifest_hash(actual_manifest)
        return {
            "valid": expected_sha256 == actual_sha256,
            "expected_sha256": expected_sha256,
            "actual_sha256": actual_sha256,
            "match": expected_sha256 == actual_sha256
        }

    def compute_file_hash(self, file_path: Path) -> str:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256()
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        return file_hash.hexdigest()

    def create_sprint_manifest_with_hash(self, sprint_data: Dict[str, Any]) -> Dict[str, Any]:
        clean_data = {k: v for k, v in sprint_data.items() if k != 'expected_sha256'}
        manifest_hash = self.compute_manifest_hash(clean_data)
        return {
            **clean_data,
            "expected_sha256": manifest_hash,
            "version": "v1",
            "hash_algorithm": "SHA-256"
        }

# Global instance
validator = DeterministicValidator()