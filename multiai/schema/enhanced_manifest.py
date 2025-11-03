
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Dict, Optional
import hashlib, json
from datetime import datetime, timezone

class ArtifactType(str, Enum):
    CODE = "code"
    TEST = "test"
    DOC = "documentation"

class RiskLevel(str, Enum):
    LOW = "low"; MEDIUM = "medium"; HIGH = "high"; CRITICAL = "critical"

class Artifact(BaseModel):
    artifact_id: str
    type: ArtifactType
    path: str
    purpose: str
    expected_behavior: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    expected_sha256: Optional[str] = None

class SprintManifest(BaseModel):
    sprint_id: str
    sprint_purpose: str
    version: str = "5.0"
    artifacts: List[Artifact]
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def calculate_manifest_hash(self) -> str:
        data = json.dumps(self.dict(), sort_keys=True).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def validate_dependencies(self) -> bool:
        visited, stack = set(), set()
        def visit(n):
            if n in stack: return False
            if n in visited: return True
            stack.add(n)
            for dep in self.dependency_graph.get(n, []):
                if not visit(dep): return False
            stack.remove(n); visited.add(n); return True
        return all(visit(a.artifact_id) for a in self.artifacts)



# 2 sinden best uret.

# schema/enhanced_manifest.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
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

    # Enhanced fields
    dependencies: List[ArtifactDependency] = Field(default_factory=list)
    expected_behavior: str = Field("", description="Expected functional behavior")
    acceptance_criteria: List[str] = Field(default_factory=list)
    risk_assessment: RiskAssessment
    compliance_requirements: List[ComplianceRequirement] = Field(default_factory=list)

    # Hash tracking
    expected_sha256: Optional[str] = Field(None, description="Pre-calculated hash")
    actual_sha256: Optional[str] = Field(None, description="Post-execution hash")

    # Metadata
    created_by: str = "system"
    estimated_effort: int = Field(0, description="Estimated story points")
    priority: int = Field(1, ge=1, le=5)

    @validator('expected_sha256')
    def validate_sha256(cls, v):
        if v and len(v) != 64:
            raise ValueError('SHA256 must be 64 characters')
        return v


class SprintManifest(BaseModel):
    sprint_id: str = Field(..., description="Unique sprint identifier")
    sprint_purpose: str = Field(..., description="Business goal")
    version: str = Field("5.0", description="Manifest schema version")

    # Enhanced artifacts
    artifacts: List[Artifact] = Field(..., description="All artifacts in this sprint")

    # Dependency graph
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict)

    # Risk & Compliance
    overall_risk: RiskAssessment
    compliance_requirements: List[ComplianceRequirement] = Field(default_factory=list)

    # Execution context
    collaboration_mode: str = Field("full-auto", description="full-auto/guided/manual")
    requires_approval: bool = Field(False)
    budget_allocation: float = Field(0.0, description="Allocated budget for this sprint")

    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = "architect_agent"
    tenant_id: Optional[str] = Field(None, description="Multi-tenant isolation")

    class Config:
        frozen = True  # Immutable for determinism

    def calculate_manifest_hash(self) -> str:
        """Calculate deterministic hash of the manifest"""
        manifest_dict = self.dict(exclude={'actual_sha256'})  # Exclude runtime fields
        manifest_json = json.dumps(manifest_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(manifest_json.encode()).hexdigest()

    def validate_dependencies(self) -> bool:
        """Validate artifact dependencies for cycles and consistency"""
        visited = set()
        recursion_stack = set()

        def has_cycle(artifact_id: str) -> bool:
            if artifact_id in recursion_stack:
                return True
            if artifact_id in visited:
                return False

            visited.add(artifact_id)
            recursion_stack.add(artifact_id)

            for dep in self.dependency_graph.get(artifact_id, []):
                if has_cycle(dep):
                    return True

            recursion_stack.remove(artifact_id)
            return False

        for artifact in self.artifacts:
            if has_cycle(artifact.artifact_id):
                return False
        return True

    def get_execution_order(self) -> List[str]:
        """Get topological sort of artifacts for execution order"""
        if not self.validate_dependencies():
            raise ValueError("Cyclic dependencies detected")

        visited = set()
        order = []

        def visit(artifact_id: str):
            if artifact_id not in visited:
                visited.add(artifact_id)
                for dep in self.dependency_graph.get(artifact_id, []):
                    visit(dep)
                order.append(artifact_id)

        for artifact in self.artifacts:
            visit(artifact.artifact_id)

        return list(reversed(order))

    def calculate_risk_score(self) -> float:
        """Calculate overall risk score for the sprint"""
        if not self.artifacts:
            return 0.0

        total_risk = sum(
            artifact.risk_assessment.score * artifact.estimated_effort
            for artifact in self.artifacts
        )
        total_effort = sum(artifact.estimated_effort for artifact in self.artifacts)

        return total_risk / total_effort if total_effort > 0 else 0.0