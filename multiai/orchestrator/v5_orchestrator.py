# orchestrator/v50_orchestrator.py
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from ..agents.researcher import EnhancedResearcherAgent
from ..agents.architect import EnhancedArchitectAgent
from ..agents.coder import EnhancedCoderAgent
from ..agents.tester import EnhancedTesterAgent
from ..agents.critic_agent import EnhancedCriticAgent
from ..agents.supervisor import EnhancedSupervisorAgent
from ..agents.budget_guard_agent import EnhancedBudgetGuardAgent
from ..agents.compliance_agent import EnhancedComplianceAgent
from ..agents.human_approval_agent import EnhancedHumanApprovalAgent

from ..core.hybrid_intelligence_router import hybrid_router
from ..core.policy_agent import policy_agent
from ..schema.enhanced_manifest import SprintManifest, Artifact, RiskLevel

logger = logging.getLogger("v50_orchestrator")


class V50EnhancedOrchestrator:
    """
    V5.0 Enhanced Orchestrator - TÜM PARÇALARI BİRLEŞTİREN ŞASİ
    Coordinates all enhanced agents for deterministic software production
    """

    def __init__(self, workdir: str = "."):
        self.workdir = workdir

        # Initialize all enhanced agents
        self.researcher = EnhancedResearcherAgent(hybrid_router)
        self.architect = EnhancedArchitectAgent(hybrid_router)
        self.coder = EnhancedCoderAgent(hybrid_router)
        self.tester = EnhancedTesterAgent(hybrid_router)
        self.critic = EnhancedCriticAgent(hybrid_router)
        self.supervisor = EnhancedSupervisorAgent(hybrid_router)
        self.budget_guard = EnhancedBudgetGuardAgent()
        self.compliance_agent = EnhancedComplianceAgent()
        self.human_approval = EnhancedHumanApprovalAgent()

        self.sprint_history: List[Dict[str, Any]] = []

        logger.info("V5.0 Enhanced Orchestrator initialized with all agents")

    async def execute_sprint(self, goal: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a complete V5.0 sprint with all enhanced agents
        """
        context = context or {}
        sprint_id = f"sprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"🚀 Starting V5.0 Enhanced Sprint: {sprint_id}")
        logger.info(f"🎯 Goal: {goal}")
        logger.info(f"📋 Context: {context}")

        try:
            # PHASE 1: RESEARCH & PLANNING
            research_result = await self._execute_research_phase(goal, context, sprint_id)
            if not research_result["success"]:
                return await self._handle_phase_failure("research", research_result, sprint_id)

            # PHASE 2: ARCHITECTURE & MANIFESTO
            manifesto = await self._execute_architecture_phase(research_result, goal, context, sprint_id)
            if not manifesto:
                return await self._handle_phase_failure("architecture", {}, sprint_id)

            # PHASE 3: EXECUTION & CODING
            execution_results = await self._execute_coding_phase(manifesto, research_result, context, sprint_id)

            # PHASE 4: VALIDATION & TESTING
            validation_results = await self._execute_validation_phase(manifesto, execution_results, context, sprint_id)

            # PHASE 5: SUPERVISION & QUALITY GATES
            final_result = await self._execute_supervision_phase(
                sprint_id, goal, manifesto, research_result, execution_results, validation_results, context
            )

            logger.info(f"✅ V5.0 Sprint Completed: {sprint_id} - Success: {final_result['success']}")
            return final_result

        except Exception as e:
            logger.error(f"❌ V5.0 Sprint Failed: {sprint_id} - Error: {e}")
            return await self._handle_sprint_failure(sprint_id, goal, e)

    async def _execute_research_phase(self, goal: str, context: Dict, sprint_id: str) -> Dict[str, Any]:
        """Execute research phase with budget and compliance checks"""
        logger.info("🔬 Phase 1: Research & Analysis")

        try:
            # Budget check
            budget_check = await self.budget_guard.record_llm_usage(
                model="gpt-4",  # Research typically uses powerful models
                provider="openai",
                tokens_used=2000,  # Estimated token usage
                context={"task_type": "research", "complexity": "high", "sprint_id": sprint_id}
            )

            if not budget_check["recorded"]:
                return {
                    "success": False,
                    "error": f"Budget constraint: {budget_check.get('reason', 'Unknown')}",
                    "phase": "research"
                }

            # Execute research
            research_result = await self.researcher.conduct_research(goal, context)

            # Compliance pre-check
            compliance_check = self.compliance_agent.analyze_research_context(research_result)
            if not compliance_check["compliant"]:
                logger.warning(f"Compliance issues in research: {compliance_check['violations']}")

            return {
                "success": True,
                "research": research_result,
                "compliance_check": compliance_check,
                "budget_used": budget_check["cost"]
            }

        except Exception as e:
            logger.error(f"Research phase failed: {e}")
            return {"success": False, "error": str(e), "phase": "research"}

    async def _execute_architecture_phase(self, research_result: Dict, goal: str, context: Dict, sprint_id: str) -> \
    Optional[SprintManifest]:
        """Execute architecture phase and create sprint manifesto"""
        logger.info("🏗️  Phase 2: Architecture & Manifesto Creation")

        try:
            # Budget check
            budget_check = await self.budget_guard.record_llm_usage(
                model="gpt-4",
                provider="openai",
                tokens_used=1500,
                context={"task_type": "architecture", "complexity": "high", "sprint_id": sprint_id}
            )

            if not budget_check["recorded"]:
                logger.error(f"Architecture phase budget constraint: {budget_check.get('reason')}")
                return None

            # Create sprint manifesto
            manifesto = await self.architect.create_sprint_manifesto(
                research_result["research"], goal, context
            )

            # Validate manifesto
            if not manifesto.validate_dependencies():
                logger.error("Manifesto dependency validation failed")
                return None

            logger.info(f"📋 Manifesto created with {len(manifesto.artifacts)} artifacts")
            return manifesto

        except Exception as e:
            logger.error(f"Architecture phase failed: {e}")
            return None

    async def _execute_coding_phase(self, manifesto: SprintManifest, research: Dict, context: Dict, sprint_id: str) -> \
    Dict[str, Any]:
        """Execute coding phase for all artifacts"""
        logger.info("💻 Phase 3: Code Implementation")

        execution_results = {}
        execution_order = manifesto.get_execution_order()

        for artifact_id in execution_order:
            artifact = next((a for a in manifesto.artifacts if a.artifact_id == artifact_id), None)
            if not artifact:
                continue

            logger.info(f"  Implementing artifact: {artifact.artifact_id} ({artifact.type})")

            try:
                # Budget check for coding
                budget_check = await self.budget_guard.record_llm_usage(
                    model="gpt-4" if artifact.risk_assessment.level in [RiskLevel.HIGH,
                                                                        RiskLevel.CRITICAL] else "gpt-3.5-turbo",
                    provider="openai",
                    tokens_used=1000,
                    context={
                        "task_type": "coding",
                        "complexity": artifact.risk_assessment.level,
                        "sprint_id": sprint_id,
                        "artifact_id": artifact_id
                    }
                )

                if not budget_check["recorded"]:
                    execution_results[artifact_id] = {
                        "status": "failed",
                        "error": f"Budget constraint: {budget_check.get('reason')}",
                        "budget_check": budget_check
                    }
                    continue

                # Implement artifact
                implementation = await self.coder.implement_artifact(
                    artifact.dict(), research["research"],
                    {**context, "artifact_id": artifact_id, "sprint_id": sprint_id}
                )

                execution_results[artifact_id] = {
                    "status": "implemented",
                    "content": implementation,
                    "artifact_type": artifact.type.value,
                    "budget_used": budget_check["cost"]
                }

            except Exception as e:
                logger.error(f"Failed to implement artifact {artifact_id}: {e}")
                execution_results[artifact_id] = {
                    "status": "failed",
                    "error": str(e),
                    "artifact_type": artifact.type.value
                }

        return execution_results

    async def _execute_validation_phase(self, manifesto: SprintManifest, execution_results: Dict, context: Dict,
                                        sprint_id: str) -> Dict[str, Any]:
        """Execute validation phase with testing and criticism"""
        logger.info("🧪 Phase 4: Validation & Testing")

        validation_results = {}

        for artifact_id, result in execution_results.items():
            if result["status"] != "implemented":
                continue

            artifact = next((a for a in manifesto.artifacts if a.artifact_id == artifact_id), None)
            if not artifact or artifact.type.value != "code":
                continue

            try:
                # Generate and run tests
                test_suite = await self.tester.create_comprehensive_tests(
                    result["content"], artifact.dict(), {},
                    {**context, "sprint_id": sprint_id}
                )

                test_results = await self.tester.execute_tests(
                    test_suite, result["content"],
                    {**context, "sprint_id": sprint_id}
                )

                # Critic analysis
                critic_analysis = await self.critic.analyze_mismatch(
                    artifact, result["content"], "initial_implementation",
                    {**context, "sprint_id": sprint_id}
                )

                validation_results[artifact_id] = {
                    "tests": test_results,
                    "critic_analysis": critic_analysis,
                    "overall_valid": (
                            test_results["summary"]["overall_status"] == "passed" and
                            not critic_analysis["requires_human_review"]
                    )
                }

            except Exception as e:
                logger.error(f"Validation failed for artifact {artifact_id}: {e}")
                validation_results[artifact_id] = {
                    "error": str(e),
                    "overall_valid": False
                }

        return validation_results

    async def _execute_supervision_phase(self, sprint_id: str, goal: str, manifesto: SprintManifest,
                                         research_result: Dict, execution_results: Dict,
                                         validation_results: Dict, context: Dict) -> Dict[str, Any]:
        """Execute final supervision phase with quality gates"""
        logger.info("👑 Phase 5: Supervision & Quality Gates")

        try:
            # Prepare sprint data for supervision
            sprint_data = {
                "sprint_id": sprint_id,
                "goal": goal,
                "manifesto": manifesto.dict(),
                "research": research_result["research"],
                "execution_results": execution_results,
                "validation_results": validation_results,
                "budget_used": await self._calculate_total_budget_used(),
                "artifact_count": len(manifesto.artifacts),
                "successful_artifacts": len([r for r in execution_results.values() if r["status"] == "implemented"])
            }

            # Execute supervision
            supervision_result = await self.supervisor.supervise_sprint(sprint_data, context)

            # Check if human approval is required
            if (supervision_result["decision"]["requires_human_review"] or
                    not supervision_result["decision"]["should_approve"]):

                approval_context = {
                    "sprint_id": sprint_id,
                    "goal": goal,
                    "supervision_result": supervision_result,
                    "quality_gates": supervision_result["quality_gates"]
                }

                human_approved = await self.human_approval.request_approval(
                    approval_context,
                    priority="high" if not supervision_result["decision"]["should_approve"] else "medium"
                )

                if not human_approved:
                    supervision_result["decision"]["overall_decision"] = "rejected"
                    supervision_result["decision"]["should_approve"] = False

            # Final sprint result
            final_result = {
                "sprint_id": sprint_id,
                "success": supervision_result["decision"]["should_approve"],
                "supervision_report": supervision_result["report"],
                "quality_gates": supervision_result["quality_gates"],
                "budget_summary": await self.budget_guard.report(),
                "compliance_summary": self.compliance_agent.get_compliance_summary(),
                "artifacts_produced": len(execution_results),
                "successful_artifacts": len([r for r in execution_results.values() if r["status"] == "implemented"]),
                "validation_results": validation_results
            }

            # Record sprint history
            self.sprint_history.append({
                **final_result,
                "timestamp": datetime.now().isoformat(),
                "goal": goal
            })

            return final_result

        except Exception as e:
            logger.error(f"Supervision phase failed: {e}")
            return await self._handle_phase_failure("supervision", {"error": str(e)}, sprint_id)

    async def _calculate_total_budget_used(self) -> float:
        """Calculate total budget used in current session"""
        budget_report = await self.budget_guard.report()
        return budget_report["budget"]["used_usd"]

    async def _handle_phase_failure(self, phase: str, result: Dict, sprint_id: str) -> Dict[str, Any]:
        """Handle phase failure gracefully"""
        error_msg = result.get("error", "Unknown error")
        logger.error(f"Phase {phase} failed: {error_msg}")

        return {
            "sprint_id": sprint_id,
            "success": False,
            "error": f"Phase {phase} failed: {error_msg}",
            "failed_phase": phase,
            "details": result
        }

    async def _handle_sprint_failure(self, sprint_id: str, goal: str, error: Exception) -> Dict[str, Any]:
        """Handle complete sprint failure"""
        return {
            "sprint_id": sprint_id,
            "success": False,
            "error": str(error),
            "goal": goal,
            "timestamp": datetime.now().isoformat()
        }

    def get_sprint_history(self) -> List[Dict[str, Any]]:
        """Get sprint execution history"""
        return self.sprint_history

    async def emergency_stop(self) -> Dict[str, Any]:
        """Emergency stop all operations"""
        logger.critical("🛑 EMERGENCY STOP ACTIVATED")

        # Stop budget guard
        budget_stop = await self.budget_guard.emergency_stop()

        # Cancel pending human approvals
        approval_cancellations = self.human_approval.cancel_pending_approvals()

        return {
            "emergency_stop": True,
            "timestamp": datetime.now().isoformat(),
            "budget_stop": budget_stop,
            "approval_cancellations": approval_cancellations,
            "message": "All V5.0 operations stopped"
        }


# Global instance
v50_orchestrator = V50EnhancedOrchestrator()