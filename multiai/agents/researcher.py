# agents/researcher.py
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime

from ..core.hybrid_router import LLM
from ..core.policy_agent import policy_agent

logger = logging.getLogger("researcher")


class EnhancedResearcherAgent:
    """
    V5.0 Enhanced Researcher Agent
    Comprehensive technology research with risk assessment and feasibility analysis
    """

    def __init__(self, llm: LLM):
        self.llm = llm
        self.policy_agent = policy_agent

    async def conduct_research(self, goal: str, context: Optional[Dict] = None) -> Dict:
        """
        Conduct comprehensive technology research
        """
        context = context or {}

        try:
            # Build enhanced research prompt
            research_prompt = self._build_research_prompt(goal, context)

            # Use hybrid router for research (typically cloud AI)
            research_text = await self.llm.complete(research_prompt, json_mode=True)
            research_data = self.llm.safe_json(research_text, self._get_fallback_research(goal))

            # Enhance research with additional analysis
            enhanced_research = await self._enhance_research_data(research_data, goal, context)

            # Validate research completeness
            validation_result = await self._validate_research(enhanced_research, goal)

            if not validation_result["valid"]:
                logger.warning(f"Research validation issues: {validation_result['issues']}")
                enhanced_research = await self._fix_research_issues(enhanced_research, validation_result["issues"])

            logger.info(
                f"Research completed for: {goal} - Tech stack: {len(enhanced_research.get('tech_stack', []))} items")

            return enhanced_research

        except Exception as e:
            logger.error(f"Research failed: {e}")
            return self._get_fallback_research(goal)

    def _build_research_prompt(self, goal: str, context: Dict) -> str:
        """Build comprehensive research prompt"""

        compliance_requirements = context.get("compliance", [])
        risk_tolerance = context.get("risk_tolerance", "medium")

        return f"""
        As an AI Senior Technology Researcher and Solution Architect, analyze this goal:

        GOAL: {goal}

        CONTEXT:
        - Risk Tolerance: {risk_tolerance}
        - Compliance Requirements: {compliance_requirements}
        - Collaboration Mode: {context.get('mode', 'full-auto')}

        RESEARCH REQUIREMENTS:

        1. TECHNOLOGY STACK ANALYSIS:
           - Recommended programming languages
           - Frameworks and libraries
           - Database solutions
           - Deployment platforms
           - Monitoring tools
           - Security tools

        2. ARCHITECTURE RECOMMENDATIONS:
           - Architectural pattern (microservices, monolith, serverless, etc.)
           - Data flow design
           - API design principles
           - Scaling strategy
           - Security architecture

        3. RISK ASSESSMENT:
           - Technical risks and mitigation strategies
           - Security risks
           - Compliance risks
           - Operational risks
           - Implementation risks

        4. REQUIREMENTS ANALYSIS:
           - Functional requirements
           - Non-functional requirements (performance, security, scalability)
           - Integration requirements
           - Compliance requirements

        5. ACCEPTANCE CRITERIA:
           - Technical acceptance criteria
           - Business acceptance criteria
           - Security acceptance criteria
           - Performance acceptance criteria

        6. FEASIBILITY ANALYSIS:
           - Implementation complexity (low/medium/high)
           - Time estimation
           - Resource requirements
           - Skill requirements

        7. ALTERNATIVES ANALYSIS:
           - Alternative approaches
           - Pros and cons of each
           - Recommendation with justification

        Return JSON with this structure:
        {{
            "tech_stack": [
                {{
                    "category": "backend|frontend|database|infrastructure|monitoring",
                    "technology": "technology name",
                    "version": "recommended version",
                    "justification": "why this technology",
                    "complexity": "low|medium|high",
                    "risk_level": "low|medium|high"
                }}
            ],
            "architecture": {{
                "pattern": "recommended pattern",
                "justification": "why this pattern",
                "components": ["list of main components"],
                "data_flow": "description of data flow",
                "scaling_strategy": "horizontal|vertical|auto"
            }},
            "requirements": {{
                "functional": ["list of functional requirements"],
                "non_functional": {{
                    "performance": "requirements",
                    "security": "requirements",
                    "scalability": "requirements",
                    "reliability": "requirements"
                }}
            }},
            "risks": [
                {{
                    "category": "technical|security|compliance|operational",
                    "description": "risk description",
                    "impact": "low|medium|high|critical",
                    "probability": "low|medium|high",
                    "mitigation": "how to mitigate"
                }}
            ],
            "acceptance_criteria": [
                "list of measurable acceptance criteria"
            ],
            "feasibility": {{
                "complexity": "low|medium|high",
                "estimated_timeline": "timeline description",
                "skill_requirements": ["required skills"],
                "resource_requirements": ["required resources"]
            }},
            "alternatives": [
                {{
                    "approach": "alternative approach",
                    "pros": ["advantages"],
                    "cons": ["disadvantages"],
                    "recommendation": "yes|no"
                }}
            ]
        }}
        """

    async def _enhance_research_data(self, research_data: Dict, goal: str, context: Dict) -> Dict:
        """Enhance research data with additional analysis"""

        enhanced = research_data.copy()

        # Add metadata
        enhanced["metadata"] = {
            "research_id": f"research_{hash(goal) % 10000:04d}",
            "goal": goal,
            "conducted_at": datetime.utcnow().isoformat(),
            "researcher_version": "5.0",
            "context": {
                "compliance": context.get("compliance", []),
                "risk_tolerance": context.get("risk_tolerance", "medium")
            }
        }

        # Calculate overall risk score
        enhanced["overall_risk"] = await self._calculate_overall_risk(enhanced)

        # Add technology compatibility analysis
        enhanced["compatibility_analysis"] = await self._analyze_technology_compatibility(enhanced)

        # Add cost estimation
        enhanced["cost_estimation"] = await self._estimate_costs(enhanced, context)

        # Add implementation roadmap
        enhanced["implementation_roadmap"] = await self._create_implementation_roadmap(enhanced)

        return enhanced

    async def _calculate_overall_risk(self, research_data: Dict) -> Dict:
        """Calculate overall project risk based on research"""
        risks = research_data.get("risks", [])

        if not risks:
            return {"level": "medium", "score": 0.5, "factors": ["No risk assessment"]}

        # Calculate weighted risk score
        impact_weights = {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 0.9}
        probability_weights = {"low": 0.1, "medium": 0.5, "high": 0.9}

        weighted_risks = []
        for risk in risks:
            impact = impact_weights.get(risk.get("impact", "medium"), 0.4)
            probability = probability_weights.get(risk.get("probability", "medium"), 0.5)
            weighted_risks.append(impact * probability)

        avg_risk = sum(weighted_risks) / len(weighted_risks) if weighted_risks else 0.5

        # Determine risk level
        if avg_risk >= 0.7:
            level = "high"
        elif avg_risk >= 0.4:
            level = "medium"
        else:
            level = "low"

        # Get top risk factors
        high_risks = [r for r in risks if r.get("impact") in ["high", "critical"]]
        risk_factors = [r["description"] for r in high_risks[:3]]  # Top 3

        return {
            "level": level,
            "score": avg_risk,
            "factors": risk_factors,
            "high_risk_count": len(high_risks)
        }

    async def _analyze_technology_compatibility(self, research_data: Dict) -> Dict:
        """Analyze technology compatibility and dependencies"""
        tech_stack = research_data.get("tech_stack", [])

        compatibility = {
            "compatible": True,
            "warnings": [],
            "dependencies": [],
            "conflicts": []
        }

        # Simple compatibility checks (in reality, this would be more sophisticated)
        technologies = [tech["technology"].lower() for tech in tech_stack]

        # Check for potential conflicts
        if "mysql" in technologies and "mongodb" in technologies:
            compatibility["warnings"].append("Mixed SQL/NoSQL databases may add complexity")

        if any(tech in technologies for tech in ["django", "flask"]) and "react" in technologies:
            compatibility["dependencies"].append("API bridge required between backend and frontend")

        # Check for missing components
        has_backend = any(tech.get("category") == "backend" for tech in tech_stack)
        has_database = any(tech.get("category") == "database" for tech in tech_stack)

        if not has_backend:
            compatibility["warnings"].append("No backend technology specified")
        if not has_database:
            compatibility["warnings"].append("No database technology specified")

        return compatibility

    async def _estimate_costs(self, research_data: Dict, context: Dict) -> Dict:
        """Estimate implementation and operational costs"""
        feasibility = research_data.get("feasibility", {})
        complexity = feasibility.get("complexity", "medium")

        # Simple cost estimation based on complexity
        cost_multipliers = {
            "low": 1.0,
            "medium": 2.0,
            "high": 4.0
        }

        base_cost = 1000  # Base cost unit
        multiplier = cost_multipliers.get(complexity, 2.0)

        return {
            "development_cost": base_cost * multiplier,
            "maintenance_cost": base_cost * multiplier * 0.2,  # 20% of dev cost annually
            "infrastructure_cost": base_cost * 0.5,
            "complexity_factor": complexity,
            "cost_units": "relative_units"
        }

    async def _create_implementation_roadmap(self, research_data: Dict) -> Dict:
        """Create high-level implementation roadmap"""
        feasibility = research_data.get("feasibility", {})
        complexity = feasibility.get("complexity", "medium")

        # Timeline estimation based on complexity
        timeline_estimates = {
            "low": "2-4 weeks",
            "medium": "1-2 months",
            "high": "3-6 months"
        }

        phases = [
            {
                "phase": "Planning & Design",
                "duration": "1-2 weeks",
                "activities": ["Detailed technical design", "Architecture finalization", "Risk mitigation planning"]
            },
            {
                "phase": "Core Development",
                "duration": timeline_estimates.get(complexity, "1-2 months"),
                "activities": ["Backend implementation", "Frontend development", "Database setup"]
            },
            {
                "phase": "Testing & QA",
                "duration": "2-3 weeks",
                "activities": ["Unit testing", "Integration testing", "Security testing", "Performance testing"]
            },
            {
                "phase": "Deployment & Launch",
                "duration": "1-2 weeks",
                "activities": ["Production deployment", "Monitoring setup", "Documentation", "Training"]
            }
        ]

        return {
            "total_timeline": timeline_estimates.get(complexity, "2-3 months"),
            "phases": phases,
            "critical_path": ["Planning & Design", "Core Development", "Testing & QA"],
            "dependencies": research_data.get("architecture", {}).get("components", [])
        }

    async def _validate_research(self, research_data: Dict, goal: str) -> Dict:
        """Validate research completeness and quality"""
        validation = {
            "valid": True,
            "issues": [],
            "warnings": []
        }

        required_sections = ["tech_stack", "architecture", "requirements", "risks"]
        for section in required_sections:
            if not research_data.get(section):
                validation["valid"] = False
                validation["issues"].append(f"Missing required section: {section}")

        # Check tech stack completeness
        tech_stack = research_data.get("tech_stack", [])
        if len(tech_stack) < 3:
            validation["warnings"].append("Technology stack seems minimal")

        # Check risk assessment
        risks = research_data.get("risks", [])
        if len(risks) < 2:
            validation["warnings"].append("Risk assessment may be incomplete")

        return validation

    async def _fix_research_issues(self, research_data: Dict, issues: List[str]) -> Dict:
        """Attempt to fix research validation issues"""
        if not issues:
            return research_data

        fix_prompt = f"""
        Fix these issues in the research data:

        CURRENT RESEARCH:
        {json.dumps(research_data, indent=2)}

        IDENTIFIED ISSUES:
        {chr(10).join(issues)}

        Return the COMPLETE fixed research data in the same JSON structure.
        """

        try:
            fixed_research = await self.llm.complete(fix_prompt, json_mode=True)
            return self.llm.safe_json(fixed_research, research_data)  # Fallback to original
        except Exception as e:
            logger.error(f"Research fix failed: {e}")
            return research_data

    def _get_fallback_research(self, goal: str) -> Dict:
        """Get fallback research when AI fails"""
        return {
            "tech_stack": [
                {
                    "category": "backend",
                    "technology": "Python/FastAPI",
                    "version": "latest",
                    "justification": "Fallback - reliable and well-documented",
                    "complexity": "medium",
                    "risk_level": "low"
                }
            ],
            "architecture": {
                "pattern": "modular monolith",
                "justification": "Fallback - simple to implement",
                "components": ["API", "Business Logic", "Data Access"],
                "data_flow": "Standard request-response",
                "scaling_strategy": "vertical"
            },
            "requirements": {
                "functional": ["Implement core functionality"],
                "non_functional": {
                    "performance": "Adequate for initial load",
                    "security": "Basic authentication and validation",
                    "scalability": "Vertical scaling capable",
                    "reliability": "Standard error handling"
                }
            },
            "risks": [
                {
                    "category": "technical",
                    "description": "Fallback mode - limited analysis",
                    "impact": "medium",
                    "probability": "high",
                    "mitigation": "Manual review required"
                }
            ],
            "acceptance_criteria": [
                "Functional implementation",
                "Basic error handling",
                "Adequate documentation"
            ],
            "feasibility": {
                "complexity": "medium",
                "estimated_timeline": "2-4 weeks",
                "skill_requirements": ["Python", "FastAPI", "Basic DevOps"],
                "resource_requirements": ["Development environment", "Testing framework"]
            },
            "metadata": {
                "research_id": "fallback",
                "goal": goal,
                "conducted_at": datetime.utcnow().isoformat(),
                "researcher_version": "5.0-fallback"
            }
        }