
import argparse
import asyncio
import logging
from pathlib import Path
from multiai.core.multi_tenant import TenantWorkspace
from multiai.core.compliance_manager import ComplianceManager
from multiai.core.enterprise_dashboard import EnterpriseDashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("multiai.cli")

async def main():
    parser = argparse.ArgumentParser(description="MultiAI Enterprise CLI")
    parser.add_argument("command", choices=["create-tenant", "check-compliance", "report"])
    parser.add_argument("--tenant", help="Tenant ID")
    args = parser.parse_args()

    workspace = TenantWorkspace(Path("tenants"))
    compliance = ComplianceManager()
    dashboard = EnterpriseDashboard()

    if args.command == "create-tenant":
        if not args.tenant:
            print("--tenant required")
            return
        tdir = workspace.create_tenant(args.tenant)
        print(f"✅ Tenant workspace created: {tdir}")

    elif args.command == "check-compliance":
        result = compliance.check_compliance("system", {"SOC2": True, "GDPR": True})
        print("✅ Compliance results:", result)

    elif args.command == "report":
        dashboard.update_metrics("demo", 12.5, 0.98)
        print("📊 Dashboard:", dashboard.generate_report())

if __name__ == "__main__":
    asyncio.run(main())
