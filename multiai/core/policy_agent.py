import yaml, logging
from dataclasses import dataclass
from typing import Dict, Optional
from pathlib import Path
log = logging.getLogger("policy")
@dataclass
class RoutingPolicy: strategy_tasks:list; execution_tasks:list; critique_tasks:list; local_models:Dict[str,str]; cloud_models:Dict[str,str]
@dataclass
class BudgetPolicy: monthly_limit:float; critical_alert:float; cost_tracking:bool
@dataclass
class SecurityPolicy: allowed_commands:list; max_file_size:int; require_approval:bool
class PolicyAgent:
    def __init__(self, policy_path: str = "policy_agent.yaml"):
        self.policy_path = Path(policy_path)
        self.routing_policy=None; self.budget_policy=None; self.security_policy=None
        self.load_policies()
    def load_policies(self):
        if not self.policy_path.exists():
            self.policy_path.write_text("policy:\n  routing: {}\n  models: {}\n  budget: {}\n  security: {}\n")
        data = yaml.safe_load(self.policy_path.read_text())
        p = data.get("policy", {}); m=p.get("models",{}); r=p.get("routing",{}); b=p.get("budget",{}); s=p.get("security",{})
        self.routing_policy = RoutingPolicy(r.get("strategy_tasks",[]), r.get("execution_tasks",[]), r.get("critique_tasks",[]), m.get("local",{}), m.get("cloud",{}))
        self.budget_policy = BudgetPolicy(b.get("monthly_limit",100.0), b.get("critical_alert",10.0), b.get("cost_tracking",True))
        self.security_policy = SecurityPolicy(s.get("allowed_commands",[]), s.get("max_file_size",10_485_760), s.get("require_approval",True))
        log.info("Policies loaded")
policy_agent = PolicyAgent()
