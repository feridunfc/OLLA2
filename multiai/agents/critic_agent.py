# agents/critic_agent.py
import hashlib
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime

from ..core.hybrid_router import LLM
from ..schema.enhanced_manifest import Artifact, RiskLevel
from ..core.policy_agent import policy_agent

logger = logging.getLogger("critic")


class EnhancedCriticAgent:
    """
    V5.0 Enhanced Critic Agent
    Advanced code analysis with security scanning, quality assessment, and auto-patching
    """

    def __init__(self, llm: LLM):
        self.llm = llm
        self.policy_agent = policy_agent

    async def analyze_mismatch(self, artifact: Artifact, actual_content: str,
                               mismatch_reason: str, context: Optional[Dict] = None) -> Dict:
        """
        Comprehensive analysis of hash mismatches with enhanced capabilities
        """
        context = context or {}

        try:
            # Calculate hashes
            expected_hash = artifact.expected_sha256
            actual_hash = hashlib.sha256(actual_content.encode()).hexdigest()

            # Build enhanced analysis prompt
            critic_prompt = self._build_critic_prompt(artifact, actual_content,
                                                      expected_hash, actual_hash,
                                                      mismatch_reason, context)

            # Get AI analysis
            analysis_text = await self.llm.complete(critic_prompt, json_mode=True)
            analysis_data = self.llm.safe_json(analysis_text, self._get_fallback_analysis())

            # Enhance analysis with additional checks
            enhanced_analysis = await self._enhance_analysis(analysis_data, artifact,
                                                             actual_content, context)

            # Generate patch if applicable
            if enhanced_analysis["should_patch"]:
                patch_result = await self._generate_patch(artifact, actual_content,
                                                          enhanced_analysis, context)
                enhanced_analysis["patch_content"] = patch_result["patch_content"]
                enhanced_analysis["patch_confidence"] = patch_result["confidence"]

            logger.info(f"Critic analysis complete: {artifact.artifact_id} - Risk: {enhanced_analysis['risk_level']}")

            return enhanced_analysis

        except Exception as e:
            logger.error(f"Critic analysis failed: {e}")
            return self._get_fallback_analysis()

    def _build_critic_prompt(self, artifact: Artifact, actual_content: str,
                             expected_hash: str, actual_hash: str,
                             mismatch_reason: str, context: Dict) -> str:
        """Build comprehensive critic analysis prompt"""

        return f"""
        As an AI Senior Code Reviewer and Security Analyst, analyze this hash mismatch:

        ARTIFACT CONTEXT:
        - ID: {artifact.artifact_id}
        - Type: {artifact.type}
        - Path: {artifact.path}
        - Purpose: {artifact.purpose}
        - Expected Behavior: {artifact.expected_behavior}
        - Risk Level: {artifact.risk_assessment.level}

        HASH MISMATCH:
        - Expected SHA256: {expected_hash}
        - Actual SHA256: {actual_hash}
        - Reason: {mismatch_reason}

        ACTUAL CONTENT:
        ```{artifact.type}
        {actual_content}
        ```

        ANALYSIS REQUIREMENTS:

        1. SECURITY ASSESSMENT:
           - Scan for security vulnerabilities
           - Check for unsafe patterns
           - Validate input handling
           - Identify information disclosure risks

        2. QUALITY ASSESSMENT:
           - Code structure and readability
           - Adherence to best practices
           - Error handling completeness
           - Documentation quality

        3. FUNCTIONAL ASSESSMENT:
           - Alignment with expected behavior
           - Completeness of implementation
           - Integration readiness
           - Test coverage implications

        4. RISK EVALUATION:
           - Business impact of mismatch
           - Security risk level
           - Operational risk
           - Compliance implications

        5. PATCH RECOMMENDATION:
           - Should we auto-patch? (yes/no)
           - Patch strategy
           - Confidence level

        CONTEXT:
        - Compliance: {context.get('compliance', [])}
        - Collaboration Mode: {context.get('mode', 'full-auto')}

        Return JSON with this structure:
        {{
            "analysis": "detailed analysis text",
            "risk_level": "low|medium|high|critical",
            "security_issues": ["list of security concerns"],
            "quality_issues": ["list of quality concerns"],
            "functional_issues": ["list of functional concerns"],
            "should_patch": true|false,
            "patch_strategy": "description of how to fix",
            "suggested_fix": "specific fix instructions",
            "confidence": 0.0-1.0,
            "requires_human_review": true|false
        }}
        """

    async def _enhance_analysis(self, analysis_data: Dict, artifact: Artifact,
                                actual_content: str, context: Dict) -> Dict:
        """Enhance AI analysis with additional checks"""

        enhanced = analysis_data.copy()

        # Add automated security scanning
        security_scan = await self._perform_security_scan(actual_content, artifact)
        enhanced["security_issues"].extend(security_scan.get("issues", []))

        # Add quality metrics
        quality_metrics = await self._calculate_quality_metrics(actual_content, artifact)
        enhanced["quality_metrics"] = quality_metrics

        # Add compliance checking
        compliance_check = await self._check_compliance(actual_content, artifact, context)
        enhanced["compliance_issues"] = compliance_check.get("issues", [])

        # Determine if human review is required
        enhanced["requires_human_review"] = self._requires_human_review(enhanced, artifact)

        # Calculate overall confidence
        enhanced["overall_confidence"] = self._calculate_confidence(enhanced)

        return enhanced

    async def _perform_security_scan(self, content: str, artifact: Artifact) -> Dict:
        """Perform automated security scanning"""
        issues = []

        # Basic pattern-based security scanning
        dangerous_patterns = [
            (r'eval\s*\(', "Use of eval() function"),
            (r'exec\s*\(', "Use of exec() function"),
            (r'__import__\s*\(', "Dynamic import usage"),
            (r'os\.system\s*\(', "Direct system command execution"),
            (r'subprocess\.call\s*\(', "Subprocess execution"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
        ]

        for pattern, description in dangerous_patterns:
            if self._search_pattern(content, pattern):
                issues.append(description)

        # Check for SQL injection patterns in specific artifact types
        if any(keyword in artifact.purpose.lower() for keyword in ['database', 'sql', 'query']):
            sql_patterns = [
                (r'f"SELECT', "f-string SQL query - potential injection"),
                (r'f"INSERT', "f-string SQL query - potential injection"),
                (r'f"UPDATE', "f-string SQL query - potential injection"),
            ]
            for pattern, description in sql_patterns:
                if self._search_pattern(content, pattern):
                    issues.append(description)

        return {"issues": issues}

    async def _calculate_quality_metrics(self, content: str, artifact: Artifact) -> Dict:
        """Calculate code quality metrics"""
        lines = content.split('\n')

        metrics = {
            "line_count": len(lines),
            "has_docstrings": any(line.strip().startswith(('"""', "'''")) for line in lines),
            "has_type_hints": "def " in content and "->" in content,
            "has_error_handling": any(keyword in content for keyword in ['try:', 'except ', 'raise ']),
            "comment_ratio": len([l for l in lines if l.strip().startswith('#')]) / max(len(lines), 1),
            "complexity_estimate": self._estimate_complexity(content)
        }

        return metrics

    async def _check_compliance(self, content: str, artifact: Artifact, context: Dict) -> Dict:
        """Check compliance requirements"""
        issues = []
        compliance_requirements = context.get("compliance", [])

        if "GDPR" in compliance_requirements:
            # Check for personal data handling
            gdpr_patterns = [
                (r'email\s*=', "Potential personal data storage"),
                (r'phone\s*=', "Potential personal data storage"),
                (r'address\s*=', "Potential personal data storage"),
                (r'personal_data', "Explicit personal data handling"),
            ]
            for pattern, description in gdpr_patterns:
                if self._search_pattern(content, pattern):
                    issues.append(f"GDPR: {description}")

        if "SOC2" in compliance_requirements:
            # Check for security controls
            if "logging" in content.lower() and "audit" not in content.lower():
                issues.append("SOC2: Logging without audit trail")

            if any(keyword in content for keyword in ['password', 'secret', 'key']) and 'encrypt' not in content:
                issues.append("SOC2: Potential unencrypted credential storage")

        return {"issues": issues}

    async def _generate_patch(self, artifact: Artifact, actual_content: str,
                              analysis: Dict, context: Dict) -> Dict:
        """Generate automated patch for identified issues"""

        if not analysis["should_patch"]:
            return {"patch_content": "", "confidence": 0.0}

        patch_prompt = f"""
        Generate a patch to fix the identified issues in this code:

        ORIGINAL CODE:
        {actual_content}

        ARTIFACT CONTEXT:
        - Purpose: {artifact.purpose}
        - Expected Behavior: {artifact.expected_behavior}
        - Type: {artifact.type}

        IDENTIFIED ISSUES:
        - Security: {analysis.get('security_issues', [])}
        - Quality: {analysis.get('quality_issues', [])}
        - Functional: {analysis.get('functional_issues', [])}

        PATCH STRATEGY:
        {analysis.get('patch_strategy', 'Fix all identified issues')}

        REQUIREMENTS:
        - Maintain original functionality
        - Fix all security issues
        - Improve code quality
        - Follow Python best practices
        - Add proper error handling
        - Include necessary documentation

        Return ONLY the complete fixed code, not just the patch.
        """

        try:
            patch_content = await self.llm.complete(patch_prompt)
            cleaned_patch = self._clean_patch_content(patch_content)

            # Validate patch quality
            patch_validation = await self._validate_patch(cleaned_patch, actual_content, artifact)

            return {
                "patch_content": cleaned_patch,
                "confidence": patch_validation["confidence"],
                "validation_issues": patch_validation["issues"]
            }

        except Exception as e:
            logger.error(f"Patch generation failed: {e}")
            return {"patch_content": "", "confidence": 0.0}

    async def _validate_patch(self, patch_content: str, original_content: str,
                              artifact: Artifact) -> Dict:
        """Validate generated patch quality"""
        validation = {
            "confidence": 0.5,  # Default medium confidence
            "issues": []
        }

        # Basic validation checks
        if not patch_content.strip():
            validation["issues"].append("Empty patch generated")
            validation["confidence"] = 0.1
            return validation

        if len(patch_content) < len(original_content) * 0.1:
            validation["issues"].append("Patch seems too short")
            validation["confidence"] = 0.3

        # Check if key components are preserved
        original_functions = self._extract_functions(original_content)
        patch_functions = self._extract_functions(patch_content)

        if len(patch_functions) < len(original_functions):
            validation["issues"].append("Some functions missing in patch")
            validation["confidence"] = max(0.2, validation["confidence"] - 0.2)

        # Adjust confidence based on issues
        if not validation["issues"]:
            validation["confidence"] = 0.8  # High confidence if no issues

        return validation

    def _requires_human_review(self, analysis: Dict, artifact: Artifact) -> bool:
        """Determine if human review is required"""
        # Always require human review for critical risk
        if analysis["risk_level"] == "critical":
            return True

        # Require review if multiple security issues
        if len(analysis.get("security_issues", [])) >= 3:
            return True

        # Require review for high-risk artifacts
        if artifact.risk_assessment.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return True

        # Require review if low confidence
        if analysis.get("confidence", 1.0) < 0.5:
            return True

        return False

    def _calculate_confidence(self, analysis: Dict) -> float:
        """Calculate overall confidence score"""
        base_confidence = 0.7

        # Adjust based on risk level
        risk_penalties = {
            "low": 0.0,
            "medium": -0.1,
            "high": -0.3,
            "critical": -0.5
        }

        base_confidence += risk_penalties.get(analysis["risk_level"], 0.0)

        # Adjust based on number of issues
        total_issues = (len(analysis.get("security_issues", [])) +
                        len(analysis.get("quality_issues", [])) +
                        len(analysis.get("functional_issues", [])))

        base_confidence -= min(0.3, total_issues * 0.05)

        return max(0.1, min(1.0, base_confidence))

    def _search_pattern(self, content: str, pattern: str) -> bool:
        """Search for pattern in content"""
        import re
        return bool(re.search(pattern, content))

    def _extract_functions(self, content: str) -> List[str]:
        """Extract function names from code"""
        import re
        function_pattern = r'def\s+(\w+)\s*\('
        return re.findall(function_pattern, content)

    def _clean_patch_content(self, patch_content: str) -> str:
        """Clean and format patch content"""
        # Remove markdown code blocks
        import re
        patch_content = re.sub(r'```(?:\w+)?\s*', '', patch_content)
        return patch_content.strip()

    def _estimate_complexity(self, content: str) -> float:
        """Estimate code complexity (simplified)"""
        lines = content.split('\n')
        if not lines:
            return 0.0

        complexity_indicators = [
            'if ', 'for ', 'while ', 'def ', 'class ',
            'try:', 'except ', 'with ', 'async '
        ]

        complex_lines = sum(1 for line in lines if any(indicator in line for indicator in complexity_indicators))
        return complex_lines / len(lines)

    def _get_fallback_analysis(self) -> Dict:
        """Get fallback analysis when AI fails"""
        return {
            "analysis": "Analysis failed - manual review required",
            "risk_level": "high",
            "security_issues": ["Analysis failure - assume worst case"],
            "quality_issues": ["Analysis system error"],
            "functional_issues": ["Unable to analyze functionality"],
            "should_patch": False,
            "patch_strategy": "Manual review required",
            "suggested_fix": "Have senior developer review the code",
            "confidence": 0.1,
            "requires_human_review": True,
            "compliance_issues": ["Analysis system compliance check failed"]
        }