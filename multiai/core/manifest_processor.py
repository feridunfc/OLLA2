
import logging, hashlib
from typing import Dict, Any
from ..schema.enhanced_manifest import SprintManifest, RiskLevel

logger = logging.getLogger("multiai.manifest_processor")
logger.setLevel(logging.INFO)

class ManifestProcessor:
    def __init__(self, workdir):
        self.workdir = workdir

    async def process_manifest(self, manifest: SprintManifest) -> Dict[str, Any]:
        results = {"schema_valid": False, "dependencies_ok": False, "risk": "low"}
        try:
            results["schema_valid"] = await self._validate_schema(manifest)
            results["dependencies_ok"] = manifest.validate_dependencies()
            results["manifest_hash"] = manifest.calculate_manifest_hash()
            results["execution_ready"] = all([results["schema_valid"], results["dependencies_ok"]])
            return results
        except Exception as e:
            logger.error("Manifest process error: %s", e)
            results["error"] = str(e)
            return results

    async def _validate_schema(self, manifest: SprintManifest) -> bool:
        ids = [a.artifact_id for a in manifest.artifacts]
        if len(ids) != len(set(ids)):
            return False
        for art in manifest.artifacts:
            if ".." in art.path: return False
        return True
