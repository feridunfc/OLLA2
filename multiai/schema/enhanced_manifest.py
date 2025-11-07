# schema/enhanced_manifest.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, timezone
import hashlib
import json


class ArtifactType(str, Enum):
    CODE = "code"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIG = "configuration"
    MIGRATION = "migration"
    SCRIPT = "script"
    DEPLOYMENT = "deployment"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceRequirement(str, Enum):
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"


class ArtifactDependency(BaseModel):
    artifact_id: str
    dependency_type: str = Field(..., description="hard/soft/temporal")
    condition: Optional[str] = None


class RiskAssessment(BaseModel):
    level: RiskLevel
    factors: List[str] = Field(default_factory=list)
    mitigation_plan: Optional[str] = None
    score: float = Field(ge=0.0, le=1.0)


class Artifact(BaseModel):
    artifact_id: str = Field(..., description="Unique identifier")
    type: ArtifactType
    path: str = Field(..., description="File path relative to project root")
    purpose: str = Field(..., description="Business/technical purpose")
    dependencies: List[ArtifactDependency] = Field(default_factory=list)
    expected_behavior: str = Field("", description="Expected functional behavior")
    acceptance_criteria: List[str] = Field(default_factory=list)
    risk_assessment: RiskAssessment
    estimated_effort: float = 0.0      # 🔧 ekle
    priority: int = 0                  # 🔧 ekle
    compliance_requirements: List[ComplianceRequirement] = Field(default_factory=list)
    expected_sha256: Optional[str] = Field(None, description="Pre-calculated hash")
    actual_sha256: Optional[str] = Field(None, description="Post-execution hash")
    created_by: str = "system"

    def calculate_expected_hash(self) -> str:
        from hashlib import sha256
        data = {
            "artifact_id": self.artifact_id,
            "type": self.type,
            "purpose": self.purpose,
            "expected_behavior": self.expected_behavior,
            "acceptance_criteria": self.acceptance_criteria,
        }
        return sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    @field_validator("expected_sha256")
    def validate_sha256(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) != 64:
            raise ValueError("SHA256 must be 64 characters")
        return v


class SprintManifest(BaseModel):
    sprint_id: str = Field(..., description="Unique sprint identifier")
    sprint_purpose: str = Field(..., description="Business goal")
    version: str = Field("5.0", description="Manifest schema version")
    artifacts: List[Artifact] = Field(..., description="All artifacts in this sprint")
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict)
    overall_risk: RiskAssessment
    compliance_requirements: List[ComplianceRequirement] = Field(default_factory=list)
    collaboration_mode: str = Field("full-auto", description="full-auto/guided/manual")
    requires_approval: bool = Field(False)
    budget_allocation: float = Field(0.0, description="Allocated budget for this sprint")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: str = "architect_agent"
    tenant_id: Optional[str] = Field(None, description="Multi-tenant isolation")

    class Config:
        frozen = True  # Immutable for determinism

    def calculate_manifest_hash(self) -> str:
        manifest_dict = self.model_dump(exclude={"actual_sha256"})
        manifest_json = json.dumps(manifest_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(manifest_json.encode()).hexdigest()

    def validate_dependencies(self) -> bool:
        visited, recursion_stack = set(), set()

        def has_cycle(aid: str) -> bool:
            if aid in recursion_stack:
                return True
            if aid in visited:
                return False
            visited.add(aid)
            recursion_stack.add(aid)
            for dep in self.dependency_graph.get(aid, []):
                if has_cycle(dep):
                    return True
            recursion_stack.remove(aid)
            return False

        return not any(has_cycle(a.artifact_id) for a in self.artifacts)

    def get_execution_order(self) -> List[str]:
        if not self.validate_dependencies():
            raise ValueError("Cyclic dependencies detected")
        visited, order = set(), []

        def visit(aid: str):
            if aid not in visited:
                visited.add(aid)
                for dep in self.dependency_graph.get(aid, []):
                    visit(dep)
                order.append(aid)

        for a in self.artifacts:
            visit(a.artifact_id)
        return list(reversed(order))

    def calculate_risk_score(self) -> float:
        if not self.artifacts:
            return 0.0
        total_risk = sum(a.risk_assessment.score * a.estimated_effort for a in self.artifacts)
        total_effort = sum(a.estimated_effort for a in self.artifacts)
        return total_risk / total_effort if total_effort > 0 else 0.0