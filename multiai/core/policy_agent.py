# multiai/core/policy_agent.py - TEK KAYNAK YÜKLEYİCİ
import os
import yaml
import logging
from pathlib import Path

class PolicyAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.policy_data = self._load_single_policy()

    def _load_single_policy(self) -> dict:
        """Load policy from single source - priority: policy_agent.yaml"""
        policy_paths = [
            Path("policy_agent.yaml"),
            Path("config/policy.yaml"),
            Path(__file__).parent.parent / "config" / "policy.yaml"
        ]

        for path in policy_paths:
            if path.exists():
                self.logger.info(f"Loading policy from: {path}")
                with open(path, 'r') as f:
                    return yaml.safe_load(f) or {}

        # Fallback to minimal policy
        self.logger.warning("No policy file found, using minimal default")
        return {
            "budget_limits": {"daily": 100, "per_sprint": 10},
            "security_rules": {"allowed_commands": ["pytest", "python"]},
            "compliance": {"require_approval": True}
        }

    def validate_request(self, prompt: str, kwargs: dict) -> dict:
        """Validate request against policy"""
        # Minimal placeholder validation for Sprint-0
        return {"allowed": True, "reason": "OK"}