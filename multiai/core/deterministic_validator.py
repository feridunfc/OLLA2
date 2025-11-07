# multiai/core/deterministic_validator.py
import hashlib
import json
from typing import Dict, Any
from pathlib import Path
import logging

class DeterministicValidator:
    def __init__(self, workdir: Path, ledger):
        self.workdir = workdir
        self.ledger = ledger
        self.logger = logging.getLogger(__name__)

    def compute_manifest_hash(self, manifest_data: Dict[str, Any]) -> str:
        """Compute SHA-256 hash ignoring meta fields like version, hash_algorithm, expected_sha256."""
        clean_data = {
            k: v
            for k, v in manifest_data.items()
            if k not in ("expected_sha256", "version", "hash_algorithm")
        }
        serialized = json.dumps(clean_data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def validate_manifest_integrity(self, expected_sha256: str, actual_manifest: Dict[str, Any]) -> Dict[str, Any]:
        actual_sha256 = self.compute_manifest_hash(actual_manifest)
        return {
            "valid": expected_sha256 == actual_sha256,
            "expected_sha256": expected_sha256,
            "actual_sha256": actual_sha256,
            "match": expected_sha256 == actual_sha256,
        }

    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a given file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()

    def create_sprint_manifest_with_hash(self, sprint_data: Dict[str, Any]) -> Dict[str, Any]:
        clean_data = {k: v for k, v in sprint_data.items() if k != "expected_sha256"}
        manifest_hash = self.compute_manifest_hash(clean_data)
        return {
            **clean_data,
            "expected_sha256": manifest_hash,
            "version": "v1",
            "hash_algorithm": "SHA-256",
        }

    def validate_artifact(self, artifact, manifest, actual_content=None) -> Dict[str, Any]:
        """
        Validate artifact by comparing its actual file hash with expected_sha256.
        Falls back to calculate_expected_hash() only if expected_sha256 is not set.
        """
        artifact_path = self.workdir / artifact.path
        try:
            # 🔧 Gerçek dosya hash'ini al
            if actual_content:
                actual_hash = hashlib.sha256(actual_content.encode()).hexdigest()
            else:
                actual_hash = self.compute_file_hash(artifact_path)

            expected_hash = artifact.expected_sha256 or artifact.calculate_expected_hash()
            match = actual_hash == expected_hash

            # ledger kaydı (duruma göre)
            self.ledger.update_artifact_hash(
                manifest.sprint_id,
                artifact.artifact_id,
                actual_hash,
                "validated" if match else "mismatch",
            )

            return {
                "artifact_id": artifact.artifact_id,
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
                "validation_passed": match,
            }

        except Exception as e:
            self.logger.error("Artifact validation failed for %s: %s", artifact.artifact_id, e)
            self.ledger.update_artifact_hash(
                manifest.sprint_id, artifact.artifact_id, None, f"error: {e}"
            )
            return {
                "artifact_id": artifact.artifact_id,
                "validation_passed": False,
                "error": str(e),
            }
