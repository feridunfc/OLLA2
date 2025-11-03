
import logging
from typing import Dict

logger = logging.getLogger("multiai.enterprise_dashboard")
logger.setLevel(logging.INFO)

class EnterpriseDashboard:
    def __init__(self):
        self.tenants_summary: Dict[str, Dict[str, float]] = {}

    def update_metrics(self, tenant_id: str, cost: float, compliance_score: float):
        self.tenants_summary[tenant_id] = {
            "cost": round(cost, 2),
            "compliance_score": round(compliance_score, 2),
        }
        logger.info("Updated dashboard metrics for %s", tenant_id)

    def generate_report(self) -> Dict[str, Dict[str, float]]:
        return self.tenants_summary
