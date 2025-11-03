# agents/architect.py
import logging
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import json

from ..core.hybrid_router import LLM
from ..schema.enhanced_manifest import SprintManifest, Artifact, ArtifactType, RiskLevel, RiskAssessment
from ..core.policy_agent import policy_agent

logger = logging.getLogger("architect")


class EnhancedArchitectAgent:
    """
    V5.0 Enhanced Architect Agent
    Advanced manifesto generation with risk assessment and dependency analysis
    """

    def __init__(self, llm: LLM):
        self.llm = llm
        self.policy_agent = policy_agent

    async def create_sprint_manifesto(self, research: dict, goal: str,
                                      context: Optional[Dict] = None) -> SprintManifest:
        """
        Create comprehensive sprint manifesto with enhanced features
        """
        context = context or {}
        collaboration_mode = context.get("mode", "full-auto")

        try:
            # Enhanced prompt with V5.0 features
            arch_prompt = self._build_architect_prompt(research, goal, context)

            # Use hybrid router for optimal model selection
            response = await self.llm.complete(arch_prompt, json_mode=True)
            manifest_data = self.llm.safe_json(response, self._get_fallback_manifest(goal))

            # Enhance with V5.0 features
            enhanced_manifest = await self._enhance_manifest_data(manifest_data, research, goal, context)

            # Convert to Pydantic model
            sprint_manifest = await self._build_sprint_manifest(enhanced_manifest, goal, collaboration_mode)

            logger.info(
                f"Architect created manifesto: {sprint_manifest.sprint_id} with {len(sprint_manifest.artifacts)} artifacts")
            return sprint_manifest

        except Exception as e:
            logger.error(f"Architect failed: {e}")
            return self._create_fallback_manifest(goal, collaboration_mode)

    def _build_architect_prompt(self, research: dict, goal: str, context: Dict) -> str:
        """Build comprehensive architect prompt"""
        return f"""
        As an AI Software Architect, create a detailed sprint plan for: {goal}

        RESEARCH ANALYSIS:
        {json.dumps(research, indent=2)}

        CONTEXT:
        - Collaboration Mode: {context.get('mode', 'full-auto')}
        - Risk Tolerance: {context.get('risk_tolerance', 'medium')}
        - Compliance Requirements: {context.get('compliance', [])}

        REQUIREMENTS:
        1. Create a comprehensive sprint manifesto with:
           - sprint_id: unique identifier
           - sprint_purpose: clear business goal
           - artifacts: list of all required components

        2. For EACH artifact, specify:
           - artifact_id: unique identifier
           - type: code/test/documentation/configuration/migration
           - path: file path relative to project root
           - purpose: clear technical/business purpose
           - dependencies: other artifacts this depends on
           - expected_behavior: functional requirements
           - acceptance_criteria: validation criteria
           - risk_level: low/medium/high/critical
           - risk_factors: specific risk reasons
           - estimated_effort: story points (1-8)
           - priority: 1-5 (5 = highest)

        3. Consider:
           - Technical dependencies between artifacts
           - Risk mitigation strategies
           - Compliance requirements
           - Testing strategy
           - Deployment considerations

        4. Return ONLY valid JSON matching this structure.

        IMPORTANT: Be specific about paths, dependencies, and risk assessments.
        """

    async def _enhance_manifest_data(self, manifest_data: Dict, research: dict, goal: str, context: Dict) -> Dict:
        """Enhance raw manifest data with advanced analysis"""

        # Add dependency analysis
        manifest_data["dependency_graph"] = await self._analyze_dependencies(manifest_data.get("artifacts", []))

        # Add risk assessment
        manifest_data["overall_risk"] = await self._assess_overall_risk(manifest_data.get("artifacts", []))

        # Add compliance requirements
        manifest_data["compliance_requirements"] = context.get("compliance", [])

        # Add metadata
        manifest_data["version"] = "5.0"
        manifest_data["created_at"] = datetime.utcnow().isoformat()
        manifest_data["created_by"] = "enhanced_architect"

        return manifest_data

    async def _analyze_dependencies(self, artifacts: List[Dict]) -> Dict[str, List[str]]:
        """Analyze and build dependency graph"""
        dependency_graph = {}

        for artifact in artifacts:
            artifact_id = artifact.get("artifact_id")
            dependencies = artifact.get("dependencies", [])

            if artifact_id:
                dependency_graph[artifact_id] = dependencies

        return dependency_graph

    async def _assess_overall_risk(self, artifacts: List[Dict]) -> Dict:
        """Assess overall project risk"""
        risk_scores = []
        risk_factors = []

        for artifact in artifacts:
            risk_level = artifact.get("risk_level", "low")
            risk_score = self._risk_level_to_score(risk_level)
            risk_scores.append(risk_score)

            if risk_level in ["high", "critical"]:
                risk_factors.extend(artifact.get("risk_factors", []))

        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.1
        overall_level = self._score_to_risk_level(avg_risk)

        return {
            "level": overall_level,
            "score": avg_risk,
            "factors": list(set(risk_factors))[:5],  # Top 5 unique factors
            "high_risk_artifacts": len([a for a in artifacts if a.get("risk_level") in ["high", "critical"]])
        }

    async def _build_sprint_manifest(self, manifest_data: Dict, goal: str, collaboration_mode: str) -> SprintManifest:
        """Build SprintManifest from enhanced data"""

        artifacts = []
        for art_data in manifest_data.get("artifacts", []):
            artifact = Artifact(
                artifact_id=art_data["artifact_id"],
                type=ArtifactType(art_data["type"]),
                path=art_data["path"],
                purpose=art_data["purpose"],
                dependencies=art_data.get("dependencies", []),
                expected_behavior=art_data.get("expected_behavior", ""),
                acceptance_criteria=art_data.get("acceptance_criteria", []),
                risk_assessment=RiskAssessment(
                    level=RiskLevel(art_data.get("risk_level", "low")),
                    factors=art_data.get("risk_factors", []),
                    score=self._risk_level_to_score(art_data.get("risk_level", "low")),
                    mitigation_plan=art_data.get("mitigation_plan")
                ),
                estimated_effort=art_data.get("estimated_effort", 1),
                priority=art_data.get("priority", 1)
            )
            artifacts.append(artifact)

        overall_risk_data = manifest_data.get("overall_risk", {})
        overall_risk = RiskAssessment(
            level=RiskLevel(overall_risk_data.get("level", "low")),
            score=overall_risk_data.get("score", 0.1),
            factors=overall_risk_data.get("factors", [])
        )

        return SprintManifest(
            sprint_id=manifest_data.get("sprint_id", f"sprint-{hashlib.sha256(goal.encode()).hexdigest()[:8]}"),
            sprint_purpose=goal,
            artifacts=artifacts,
            dependency_graph=manifest_data.get("dependency_graph", {}),
            overall_risk=overall_risk,
            compliance_requirements=manifest_data.get("compliance_requirements", []),
            collaboration_mode=collaboration_mode,
            requires_approval=overall_risk.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        )

    def _risk_level_to_score(self, risk_level: str) -> float:
        """Convert risk level to numerical score"""
        risk_scores = {
            "low": 0.1,
            "medium": 0.4,
            "high": 0.7,
            "critical": 0.9
        }
        return risk_scores.get(risk_level, 0.1)

    def _score_to_risk_level(self, score: float) -> str:
        """Convert numerical score to risk level"""
        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"

    def _get_fallback_manifest(self, goal: str) -> Dict:
        """Get fallback manifest data"""
        return {
            "sprint_id": f"fallback-{hashlib.sha256(goal.encode()).hexdigest()[:8]}",
            "sprint_purpose": goal,
            "artifacts": [],
            "overall_risk": {"level": "medium", "score": 0.5, "factors": ["fallback_mode"]}
        }

    def _create_fallback_manifest(self, goal: str, collaboration_mode: str) -> SprintManifest:
        """Create fallback manifest when AI fails"""
        return SprintManifest(
            sprint_id=f"error-fallback-{hashlib.sha256(goal.encode()).hexdigest()[:8]}",
            sprint_purpose=goal,
            artifacts=[],
            overall_risk=RiskAssessment(level=RiskLevel.HIGH, score=0.8, factors=["architect_failure"]),
            collaboration_mode=collaboration_mode,
            requires_approval=True
        )
