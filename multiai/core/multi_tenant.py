
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger("multiai.multi_tenant")
logger.setLevel(logging.INFO)

class TenantWorkspace:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info("TenantWorkspace initialized at %s", self.base_path)

    def create_tenant(self, tenant_id: str) -> Path:
        tdir = self.base_path / tenant_id
        tdir.mkdir(exist_ok=True)
        (tdir / "logs").mkdir(exist_ok=True)
        (tdir / "data").mkdir(exist_ok=True)
        logger.info("Created tenant workspace for %s", tenant_id)
        return tdir

    def list_tenants(self) -> Dict[str, str]:
        return {p.name: str(p) for p in self.base_path.iterdir() if p.is_dir()}
