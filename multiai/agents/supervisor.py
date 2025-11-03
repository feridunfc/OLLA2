# agents/supervisor.py
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
import hashlib

from ..core.hybrid_router import LLM
from ..core.policy_agent import policy_agent
from ..schema.enhanced_manifest import SprintManifest

logger = logging.getLogger("supervisor")


class EnhancedSupervisorAgent:
    """
    V5.0 Enhanced Supervisor Agent
    Comprehensive sprint supervision with quality gates and decision making
    """

    def __init__(self, llm: LLM):
        self.llm = llm
        self.policy_agent = policy_agent

    async def supervise_sprint(self, sprint_data: Dict, context: Optional[Dict] = None) -> Dict:
        """
        Comprehensive sprint supervision and quality assessment
        """
        context = context or {}

        try:
            # Build comprehensive supervision prompt
            supervision_prompt = self._build_supervision_prompt(sprint_data, context)

            # Get AI analysis
            analysis_text = await self.llm.complete(supervision_prompt, json_mode=True)
            analysis_data = self.llm.safe_json(analysis_text, self._get_fallback_analysis())

            # Enhance with automated metrics
            enhanced_analysis = await self._enhance_supervision_analysis(analysis_data, sprint_data, context)

            # Make go/no-go decision
            decision = await self._make_sprint_decision(enhanced_analysis, sprint_data, context)

            # Generate comprehensive report
            report = await self._generate_supervision_report(enhanced_analysis, decision, sprint_data, context)

            logger.info(
                f"Sprint supervision completed: {decision['overall_decision']} - Confidence: {decision['confidence']}")

            return {
                "analysis": enhanced_analysis,
                "decision": decision,
                "report": report,
                "recommendations": enhanced_analysis["recommendations"],
                "quality_gates": await self._assess_quality_gates(enhanced_analysis, sprint_data)
            }

        except Exception as e:
            logger.error(f"Sprint supervision failed: {e}")
            return self._get_fallback_supervision(sprint_data, str(e))

    def _build_supervision_prompt(self, sprint_data: Dict, context: Dict) -> str:
        """Build comprehensive supervision prompt"""

        return f"""
        As an AI Senior Project Supervisor and Quality Assurance Lead, analyze this sprint:

        SPRINT DATA:
        {json.dumps(sprint_data, indent=2, default=str)}

        CONTEXT:
        - Collaboration Mode: {context.get('mode', 'full-auto')}
        - Risk Tolerance: {context.get('risk_tolerance', 'medium')}
        - Compliance Requirements: {context.get('compliance', [])}

        SUPERVISION REQUIREMENTS:

        1. QUALITY ASSESSMENT:
           - Code quality and adherence to standards
           - Test coverage and effectiveness
           - Security implementation quality
           - Documentation completeness
           - Performance considerations

        2. RISK EVALUATION:
           - Technical debt accumulation
           - Security vulnerabilities
           - Compliance gaps
           - Operational risks
           - Maintenance concerns

        3. SUCCESS METRICS:
           - Requirements fulfillment
           - Acceptance criteria met
           - Stakeholder satisfaction
           - Business value delivered
           - Technical excellence

        4. IMPROVEMENT RECOMMENDATIONS:
           - Immediate actions required
           - Medium-term improvements
           - Long-term strategic changes
           - Process optimizations
           - Team development areas

        5. DECISION FRAMEWORK:
           - Should this sprint be approved?
           - What are the key risks?
           - What verification is needed?
           - What are the alternatives?

        Return JSON with this structure:
        {{
            "quality_assessment": {{
                "overall_score": 0-100,
                "code_quality": "excellent|good|fair|poor",
                "test_quality": "excellent|good|fair|poor",
                "security_quality": "excellent|good|fair|poor",
                "documentation_quality": "excellent|good|fair|poor",
                "performance_quality": "excellent|good|fair|poor"
            }},
            "risk_evaluation": {{
                "overall_risk": "low|medium|high|critical",
                "technical_debt": "low|medium|high",
                "security_risks": ["list of security concerns"],
                "compliance_gaps": ["list of compliance issues"],
                "operational_risks": ["list of operational concerns"]
            }},
            "success_metrics": {{
                "requirements_fulfillment": 0-100,
                "acceptance_criteria_met": 0-100,
                "stakeholder_satisfaction": "low|medium|high",
                "business_value": "low|medium|high",
                "technical_excellence": "low|medium|high"
            }},
            "recommendations": {{
                "immediate_actions": ["list of urgent actions"],
                "medium_term_improvements": ["list of medium-term improvements"],
                "long_term_strategic": ["list of strategic changes"],
                "process_optimizations": ["list of process improvements"]
            }},
            "decision_framework": {{
                "should_approve": true|false,
                "key_risks": ["list of critical risks"],
                "verification_needed": ["list of verification steps"],
                "alternatives": ["list of alternative approaches"]
            }},
            "confidence": 0.0-1.0
        }}
        """

    async def _enhance_supervision_analysis(self, analysis: Dict, sprint_data: Dict, context: Dict) -> Dict:
        """Enhance AI analysis with automated metrics"""

        enhanced = analysis.copy()

        # Add automated quality metrics
        enhanced["automated_metrics"] = await self._calculate_automated_metrics(sprint_data)

        # Add compliance checking
        enhanced["compliance_check"] = await self._check_compliance(sprint_data, context)

        # Add security assessment
        enhanced["security_assessment"] = await self._assess_security(sprint_data)

        # Add cost-benefit analysis
        enhanced["cost_benefit_analysis"] = await self._analyze_cost_benefit(sprint_data, context)

        # Calculate overall confidence
        enhanced["overall_confidence"] = self._calculate_overall_confidence(enhanced)

        return enhanced

    async def _calculate_automated_metrics(self, sprint_data: Dict) -> Dict:
        """Calculate automated quality metrics"""
        metrics = {
            "test_coverage": 0.0,
            "code_complexity": "unknown",
            "security_issues": 0,
            "performance_metrics": {},
            "documentation_coverage": 0.0
        }

        # Extract metrics from sprint data (simplified)
        if "test_results" in sprint_data:
            metrics["test_coverage"] = sprint_data["test_results"].get("summary", {}).get("pass_rate", 0)

        if "artifact_metrics" in sprint_data:
            artifacts = sprint_data["artifact_metrics"]
            metrics["security_issues"] = sum(art.get("security_issues", 0) for art in artifacts)

        # Calculate documentation coverage (simplified)
        total_artifacts = len(sprint_data.get("artifacts", []))
        documented_artifacts = sum(1 for art in sprint_data.get("artifacts", [])
                                   if art.get("documentation", "").strip())

        if total_artifacts > 0:
            metrics["documentation_coverage"] = (documented_artifacts / total_artifacts) * 100

        return metrics

    async def _check_compliance(self, sprint_data: Dict, context: Dict) -> Dict:
        """Check compliance requirements"""
        compliance_requirements = context.get("compliance", [])
        issues = []

        for requirement in compliance_requirements:
            if requirement == "SOC2" and not self._has_security_controls(sprint_data):
                issues.append("SOC2: Insufficient security controls documented")

            if requirement == "GDPR" and not self._has_data_protection(sprint_data):
                issues.append("GDPR: Data protection measures not evident")

            if requirement == "ISO27001" and not self._has_risk_assessment(sprint_data):
                issues.append("ISO27001: Formal risk assessment missing")

        return {
            "requirements_checked": compliance_requirements,
            "issues": issues,
            "compliance_score": 100 - (len(issues) * 20)  # Simple scoring
        }

    async def _assess_security(self, sprint_data: Dict) -> Dict:
        """Assess security implementation"""
        security_indicators = {
            "authentication": any("auth" in str(art).lower() for art in sprint_data.get("artifacts", [])),
            "encryption": any("encrypt" in str(art).lower() for art in sprint_data.get("artifacts", [])),
            "input_validation": any("validate" in str(art).lower() for art in sprint_data.get("artifacts", [])),
            "logging": any("log" in str(art).lower() for art in sprint_data.get("artifacts", [])),
        }

        security_score = sum(1 for indicator in security_indicators.values() if indicator) / len(
            security_indicators) * 100

        return {
            "indicators": security_indicators,
            "score": security_score,
            "level": "high" if security_score >= 80 else "medium" if security_score >= 60 else "low"
        }

    async def _analyze_cost_benefit(self, sprint_data: Dict, context: Dict) -> Dict:
        """Analyze cost-benefit of the sprint"""
        # Simplified cost-benefit analysis
        estimated_value = sprint_data.get("business_value", 50)  # Default medium value
        estimated_cost = sprint_data.get("actual_cost", 1000)  # Default cost

        roi = (estimated_value - estimated_cost) / estimated_cost * 100 if estimated_cost > 0 else 0

        return {
            "estimated_value": estimated_value,
            "estimated_cost": estimated_cost,
            "return_on_investment": roi,
            "efficiency": "high" if roi > 50 else "medium" if roi > 0 else "low",
            "recommendation": "proceed" if roi > 0 else "reconsider"
        }

    async def _make_sprint_decision(self, analysis: Dict, sprint_data: Dict, context: Dict) -> Dict:
        """Make go/no-go decision for the sprint"""

        quality_score = analysis["quality_assessment"]["overall_score"]
        risk_level = analysis["risk_evaluation"]["overall_risk"]
        confidence = analysis["overall_confidence"]

        # Decision matrix
        should_approve = (
                quality_score >= 70 and
                risk_level in ["low", "medium"] and
                confidence >= 0.7
        )

        decision_reasons = []
        if quality_score < 70:
            decision_reasons.append(f"Quality score too low: {quality_score}")
        if risk_level in ["high", "critical"]:
            decision_reasons.append(f"Risk level too high: {risk_level}")
        if confidence < 0.7:
            decision_reasons.append(f"Confidence too low: {confidence}")

        return {
            "overall_decision": "approved" if should_approve else "rejected",
            "should_approve": should_approve,
            "confidence": confidence,
            "decision_reasons": decision_reasons,
            "quality_gate": "passed" if should_approve else "failed",
            "required_actions": analysis["recommendations"]["immediate_actions"] if not should_approve else []
        }

    async def _generate_supervision_report(self, analysis: Dict, decision: Dict,
                                           sprint_data: Dict, context: Dict) -> Dict:
        """Generate comprehensive supervision report"""

        return {
            "executive_summary": {
                "sprint_id": sprint_data.get("sprint_id", "unknown"),
                "decision": decision["overall_decision"],
                "quality_score": analysis["quality_assessment"]["overall_score"],
                "risk_level": analysis["risk_evaluation"]["overall_risk"],
                "key_findings": analysis["decision_framework"]["key_risks"][:3],  # Top 3 risks
                "recommendation": "APPROVE" if decision["should_approve"] else "REJECT"
            },
            "detailed_analysis": {
                "quality_breakdown": analysis["quality_assessment"],
                "risk_breakdown": analysis["risk_evaluation"],
                "success_metrics": analysis["success_metrics"],
                "automated_metrics": analysis["automated_metrics"]
            },
            "recommendations": {
                "immediate": analysis["recommendations"]["immediate_actions"],
                "strategic": analysis["recommendations"]["long_term_strategic"],
                "process": analysis["recommendations"]["process_optimizations"]
            },
            "next_steps": await self._determine_next_steps(decision, analysis, context),
            "metadata": {
                "report_generated": datetime.utcnow().isoformat(),
                "supervisor_version": "5.0",
                "decision_confidence": decision["confidence"]
            }
        }

    async def _assess_quality_gates(self, analysis: Dict, sprint_data: Dict) -> Dict:
        """Assess quality gates for the sprint"""
        gates = {
            "code_quality": analysis["quality_assessment"]["code_quality"] in ["excellent", "good"],
            "test_quality": analysis["quality_assessment"]["test_quality"] in ["excellent", "good"],
            "security_quality": analysis["quality_assessment"]["security_quality"] in ["excellent", "good"],
            "documentation_quality": analysis["quality_assessment"]["documentation_quality"] in ["excellent", "good"],
            "risk_level": analysis["risk_evaluation"]["overall_risk"] in ["low", "medium"],
            "compliance": len(analysis["compliance_check"]["issues"]) == 0
        }

        passed_gates = sum(1 for passed in gates.values() if passed)
        total_gates = len(gates)

        return {
            "gates": gates,
            "passed_gates": passed_gates,
            "total_gates": total_gates,
            "pass_rate": (passed_gates / total_gates) * 100,
            "overall_status": "passed" if passed_gates == total_gates else "failed"
        }

    async def _determine_next_steps(self, decision: Dict, analysis: Dict, context: Dict) -> List[str]:
        """Determine next steps based on decision"""
        if decision["should_approve"]:
            return [
                "Proceed with deployment",
                "Update documentation",
                "Notify stakeholders",
                "Schedule post-implementation review"
            ]
        else:
            return [
                "Address immediate actions from recommendations",
                "Re-run quality gates after fixes",
                "Schedule re-review meeting",
                "Update project timeline accordingly"
            ]

    def _has_security_controls(self, sprint_data: Dict) -> bool:
        """Check if security controls are present"""
        return any(
            "security" in str(art).lower() or
            "auth" in str(art).lower() or
            "encrypt" in str(art).lower()
            for art in sprint_data.get("artifacts", [])
        )

    def _has_data_protection(self, sprint_data: Dict) -> bool:
        """Check if data protection measures are present"""
        return any(
            "data" in str(art).lower() and
            ("protect" in str(art).lower() or "privacy" in str(art).lower())
            for art in sprint_data.get("artifacts", [])
        )

    def _has_risk_assessment(self, sprint_data: Dict) -> bool:
        """Check if risk assessment is present"""
        return "risk_assessment" in sprint_data

    def _calculate_overall_confidence(self, analysis: Dict) -> float:
        """Calculate overall confidence score"""
        base_confidence = analysis.get("confidence", 0.7)

        # Adjust based on automated metrics
        automated_metrics = analysis.get("automated_metrics", {})
        if automated_metrics.get("test_coverage", 0) < 50:
            base_confidence -= 0.2

        if automated_metrics.get("security_issues", 0) > 0:
            base_confidence -= 0.1

        # Adjust based on compliance
        compliance_check = analysis.get("compliance_check", {})
        if compliance_check.get("issues"):
            base_confidence -= len(compliance_check["issues"]) * 0.05

        return max(0.1, min(1.0, base_confidence))

    def _get_fallback_analysis(self) -> Dict:
        """Get fallback analysis when AI fails"""
        return {
            "quality_assessment": {
                "overall_score": 50,
                "code_quality": "fair",
                "test_quality": "fair",
                "security_quality": "fair",
                "documentation_quality": "fair",
                "performance_quality": "fair"
            },
            "risk_evaluation": {
                "overall_risk": "medium",
                "technical_debt": "medium",
                "security_risks": ["Analysis failed - assume medium risk"],
                "compliance_gaps": ["Analysis system failure"],
                "operational_risks": ["Supervision system unavailable"]
            },
            "success_metrics": {
                "requirements_fulfillment": 50,
                "acceptance_criteria_met": 50,
                "stakeholder_satisfaction": "medium",
                "business_value": "medium",
                "technical_excellence": "medium"
            },
            "recommendations": {
                "immediate_actions": ["Manual review required due to system failure"],
                "medium_term_improvements": ["Improve supervision system reliability"],
                "long_term_strategic": ["Implement redundant supervision mechanisms"],
                "process_optimizations": ["Add manual quality gates"]
            },
            "decision_framework": {
                "should_approve": False,
                "key_risks": ["Supervision system failure", "Unable to assess quality"],
                "verification_needed": ["Manual code review", "Stakeholder validation"],
                "alternatives": ["Manual supervision", "External audit"]
            },
            "confidence": 0.1
        }

    def _get_fallback_supervision(self, sprint_data: Dict, error: str) -> Dict:
        """Get fallback supervision results"""
        return {
            "analysis": self._get_fallback_analysis(),
            "decision": {
                "overall_decision": "rejected",
                "should_approve": False,
                "confidence": 0.1,
                "decision_reasons": [f"Supervision system error: {error}"],
                "quality_gate": "failed",
                "required_actions": ["Manual review required due to system failure"]
            },
            "report": {
                "executive_summary": {
                    "sprint_id": sprint_data.get("sprint_id", "unknown"),
                    "decision": "rejected",
                    "quality_score": 50,
                    "risk_level": "high",
                    "key_findings": ["Supervision system failure"],
                    "recommendation": "REJECT"
                },
                "error": error
            },
            "recommendations": ["Manual review required due to system failure"],
            "quality_gates": {
                "overall_status": "failed",
                "pass_rate": 0,
                "error": error
            }
        }