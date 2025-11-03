# agents/debugger.py
import logging
from typing import Dict, List, Optional
import re
import traceback

from ..core.hybrid_router import LLM
from ..utils.secure_sandbox import SecureSandboxRunner

logger = logging.getLogger("debugger")


class EnhancedDebuggerAgent:
    """
    V5.0 Enhanced Debugger Agent
    Advanced debugging with root cause analysis and automated fixes
    """

    def __init__(self, llm: LLM):
        self.llm = llm
        self.sandbox = SecureSandboxRunner()

    async def diagnose_and_fix(self, code: str, error_logs: str,
                               test_results: Optional[Dict] = None,
                               context: Optional[Dict] = None) -> Dict:
        """
        Comprehensive debugging with root cause analysis
        """
        context = context or {}

        try:
            # Analyze the error and code
            analysis = await self._analyze_error(code, error_logs, test_results, context)

            # Generate fix based on analysis
            if analysis["should_attempt_fix"]:
                fix_result = await self._generate_fix(code, error_logs, analysis, context)

                # Validate the fix
                validation_result = await self._validate_fix(fix_result["fixed_code"], code, context)

                return {
                    "success": validation_result["valid"],
                    "original_code": code,
                    "fixed_code": fix_result["fixed_code"],
                    "analysis": analysis,
                    "fix_strategy": fix_result["strategy"],
                    "confidence": fix_result["confidence"],
                    "validation_result": validation_result,
                    "applied_patches": fix_result.get("patches", []),
                    "requires_human_review": analysis["requires_human_review"]
                }
            else:
                return {
                    "success": False,
                    "original_code": code,
                    "fixed_code": code,
                    "analysis": analysis,
                    "fix_strategy": "Manual fix required",
                    "confidence": 0.0,
                    "requires_human_review": True,
                    "reason": "Automatic fix not recommended"
                }

        except Exception as e:
            logger.error(f"Debugging failed: {e}")
            return self._get_fallback_result(code, error_logs, str(e))

    async def _analyze_error(self, code: str, error_logs: str,
                             test_results: Optional[Dict], context: Dict) -> Dict:
        """Comprehensive error analysis"""

        analysis_prompt = f"""
        As an AI Senior Debugging Engineer, analyze this error:

        CODE:
        {code}

        ERROR LOGS:
        {error_logs}

        TEST RESULTS:
        {test_results if test_results else "No test results available"}

        CONTEXT:
        - Artifact Type: {context.get('artifact_type', 'code')}
        - Purpose: {context.get('purpose', 'Unknown')}
        - Risk Level: {context.get('risk_level', 'medium')}

        ANALYSIS REQUIREMENTS:

        1. ROOT CAUSE ANALYSIS:
           - Identify the exact line causing the issue
           - Determine the type of error (syntax, runtime, logical, etc.)
           - Trace the error through the code flow
           - Identify any underlying architectural issues

        2. IMPACT ASSESSMENT:
           - Severity of the issue (blocking/non-blocking)
           - Scope of impact (localized/system-wide)
           - Data corruption risk
           - Security implications

        3. FIX FEASIBILITY:
           - Can this be automatically fixed? (yes/no)
           - Complexity of the fix (simple/complex)
           - Risk of introducing new issues
           - Recommended fix strategy

        4. PREVENTION RECOMMENDATIONS:
           - Code patterns to avoid
           - Testing strategies to catch similar issues
           - Monitoring improvements
           - Code review focus areas

        Return JSON with this structure:
        {{
            "root_cause": {{
                "type": "syntax|runtime|logical|resource|security",
                "description": "detailed cause description",
                "line_number": "estimated line number",
                "code_snippet": "offending code snippet",
                "underlying_issue": "deeper architectural issue if any"
            }},
            "impact": {{
                "severity": "low|medium|high|critical",
                "scope": "localized|module|system",
                "data_risk": "none|low|medium|high",
                "security_risk": "none|low|medium|high"
            }},
            "fix_feasibility": {{
                "automatic_fix_possible": true|false,
                "complexity": "simple|moderate|complex",
                "estimated_effort": "effort estimate",
                "risk_of_regression": "low|medium|high",
                "recommended_strategy": "fix strategy description"
            }},
            "prevention_recommendations": [
                "list of prevention strategies"
            ],
            "should_attempt_fix": true|false,
            "requires_human_review": true|false,
            "confidence": 0.0-1.0
        }}
        """

        analysis_text = await self.llm.complete(analysis_prompt, json_mode=True)
        analysis_data = self.llm.safe_json(analysis_text, self._get_fallback_analysis())

        # Enhance with automated code analysis
        enhanced_analysis = await self._enhance_analysis(analysis_data, code, error_logs, context)

        return enhanced_analysis

    async def _enhance_analysis(self, analysis: Dict, code: str, error_logs: str, context: Dict) -> Dict:
        """Enhance AI analysis with automated checks"""

        enhanced = analysis.copy()

        # Add automated code quality checks
        quality_checks = await self._perform_quality_checks(code, error_logs)
        enhanced["quality_issues"] = quality_checks.get("issues", [])

        # Add security scan
        security_scan = await self._scan_security_issues(code, error_logs)
        enhanced["security_issues"] = security_scan.get("issues", [])

        # Adjust confidence based on automated checks
        if quality_checks["issues"] or security_scan["issues"]:
            enhanced["confidence"] = max(0.3, enhanced.get("confidence", 0.7) - 0.2)

        # Determine if human review is required
        enhanced["requires_human_review"] = self._requires_human_review(enhanced, context)

        return enhanced

    async def _perform_quality_checks(self, code: str, error_logs: str) -> Dict:
        """Perform automated code quality checks"""
        issues = []

        # Check for common Python issues
        if 'import *' in code:
            issues.append("Wildcard import - can cause namespace pollution")

        if 'except:' in code or 'except Exception:' in code:
            issues.append("Bare except clause - can mask errors")

        if 'eval(' in code or 'exec(' in code:
            issues.append("Use of eval/exec - security risk")

        # Check for potential infinite loops
        loop_patterns = [
            (r'while\s+True\s*:', "Potential infinite while True loop"),
            (r'for\s+\w+\s+in\s+.*:\s*while\s+True', "Nested infinite loop")
        ]

        for pattern, description in loop_patterns:
            if re.search(pattern, code):
                issues.append(description)

        return {"issues": issues}

    async def _scan_security_issues(self, code: str, error_logs: str) -> Dict:
        """Scan for security issues in the code"""
        issues = []

        security_patterns = [
            (r'subprocess\.call\([^)]+shell=True', "Shell injection vulnerability"),
            (r'os\.system\(', "Direct system command execution"),
            (r'pickle\.loads\(', "Unsafe deserialization"),
            (r'input\(\)', "Unvalidated user input"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
        ]

        for pattern, description in security_patterns:
            if re.search(pattern, code):
                issues.append(description)

        return {"issues": issues}

    async def _generate_fix(self, code: str, error_logs: str, analysis: Dict, context: Dict) -> Dict:
        """Generate automated fix for the identified issues"""

        fix_prompt = f"""
        Generate a fix for this code based on the analysis:

        ORIGINAL CODE:
        {code}

        ERROR LOGS:
        {error_logs}

        ANALYSIS:
        {json.dumps(analysis, indent=2)}

        FIX REQUIREMENTS:
        - Fix the root cause identified in the analysis
        - Maintain original functionality
        - Follow Python best practices
        - Add proper error handling
        - Include necessary comments
        - Ensure code readability
        - Address any security concerns

        FIX STRATEGY:
        {analysis.get('fix_feasibility', {}).get('recommended_strategy', 'Comprehensive fix')}

        Return ONLY the complete fixed code.
        """

        try:
            fixed_code = await self.llm.complete(fix_prompt)
            cleaned_fix = self._clean_fixed_code(fixed_code)

            # Extract patches for documentation
            patches = await self._extract_patches(code, cleaned_fix)

            # Calculate confidence
            confidence = await self._calculate_fix_confidence(code, cleaned_fix, analysis, context)

            return {
                "fixed_code": cleaned_fix,
                "strategy": analysis.get('fix_feasibility', {}).get('recommended_strategy', 'AI-generated fix'),
                "patches": patches,
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"Fix generation failed: {e}")
            return {
                "fixed_code": code,
                "strategy": "Fix generation failed",
                "patches": [],
                "confidence": 0.0
            }

    async def _extract_patches(self, original_code: str, fixed_code: str) -> List[Dict]:
        """Extract and document the changes made"""
        # Simple line-based diff (in production, use proper diff library)
        original_lines = original_code.split('\n')
        fixed_lines = fixed_code.split('\n')

        patches = []

        # Simple change detection
        for i, (orig, fix) in enumerate(zip(original_lines, fixed_lines)):
            if orig != fix:
                patches.append({
                    "line": i + 1,
                    "original": orig,
                    "fixed": fix,
                    "change_type": "modification"
                })

        # Handle added/removed lines
        if len(original_lines) != len(fixed_lines):
            if len(fixed_lines) > len(original_lines):
                patches.append({
                    "line": "multiple",
                    "original": f"{len(original_lines)} lines",
                    "fixed": f"{len(fixed_lines)} lines",
                    "change_type": "lines_added"
                })
            else:
                patches.append({
                    "line": "multiple",
                    "original": f"{len(original_lines)} lines",
                    "fixed": f"{len(fixed_lines)} lines",
                    "change_type": "lines_removed"
                })

        return patches

    async def _calculate_fix_confidence(self, original_code: str, fixed_code: str,
                                        analysis: Dict, context: Dict) -> float:
        """Calculate confidence in the generated fix"""
        base_confidence = analysis.get("confidence", 0.5)

        # Adjust based on code changes
        if original_code == fixed_code:
            return 0.1  # No changes made

        # Adjust based on complexity
        complexity = analysis.get("fix_feasibility", {}).get("complexity", "moderate")
        complexity_penalties = {"simple": 0.0, "moderate": -0.1, "complex": -0.3}
        base_confidence += complexity_penalties.get(complexity, 0.0)

        # Adjust based on risk
        risk_penalty = analysis.get("fix_feasibility", {}).get("risk_of_regression", "medium")
        risk_penalties = {"low": 0.0, "medium": -0.2, "high": -0.4}
        base_confidence += risk_penalties.get(risk_penalty, 0.0)

        return max(0.1, min(1.0, base_confidence))

    async def _validate_fix(self, fixed_code: str, original_code: str, context: Dict) -> Dict:
        """Validate the generated fix"""
        validation = {
            "valid": True,
            "issues": [],
            "warnings": []
        }

        # Basic validation
        if not fixed_code.strip():
            validation["valid"] = False
            validation["issues"].append("Empty fix generated")
            return validation

        # Check if fix is substantially different from original
        if fixed_code == original_code:
            validation["valid"] = False
            validation["issues"].append("No changes made in fix")
            return validation

        # Check for basic Python syntax (simplified)
        try:
            compile(fixed_code, '<string>', 'exec')
        except SyntaxError as e:
            validation["valid"] = False
            validation["issues"].append(f"Syntax error in fix: {e}")

        # Check for obvious issues
        if 'FIXME' in fixed_code or 'TODO' in fixed_code:
            validation["warnings"].append("Fix contains TODO/FIXME comments")

        return validation

    def _requires_human_review(self, analysis: Dict, context: Dict) -> bool:
        """Determine if human review is required"""
        # Always review critical issues
        if analysis.get("impact", {}).get("severity") == "critical":
            return True

        # Review if automatic fix not recommended
        if not analysis.get("should_attempt_fix", False):
            return True

        # Review if low confidence
        if analysis.get("confidence", 1.0) < 0.5:
            return True

        # Review for high-risk artifacts
        if context.get("risk_level") in ["high", "critical"]:
            return True

        return False

    def _clean_fixed_code(self, fixed_code: str) -> str:
        """Clean and format the fixed code"""
        # Remove markdown code blocks
        fixed_code = re.sub(r'```(?:\w+)?\s*', '', fixed_code)
        return fixed_code.strip()

    def _get_fallback_analysis(self) -> Dict:
        """Get fallback analysis when AI fails"""
        return {
            "root_cause": {
                "type": "unknown",
                "description": "Analysis failed - manual investigation required",
                "line_number": "unknown",
                "code_snippet": "unknown",
                "underlying_issue": "Analysis system failure"
            },
            "impact": {
                "severity": "high",
                "scope": "unknown",
                "data_risk": "unknown",
                "security_risk": "unknown"
            },
            "fix_feasibility": {
                "automatic_fix_possible": False,
                "complexity": "unknown",
                "estimated_effort": "unknown",
                "risk_of_regression": "high",
                "recommended_strategy": "Manual debugging required"
            },
            "should_attempt_fix": False,
            "requires_human_review": True,
            "confidence": 0.1
        }

    def _get_fallback_result(self, code: str, error_logs: str, error: str) -> Dict:
        """Get fallback result when debugging fails"""
        return {
            "success": False,
            "original_code": code,
            "fixed_code": code,
            "analysis": self._get_fallback_analysis(),
            "fix_strategy": "Debugging system failure",
            "confidence": 0.0,
            "requires_human_review": True,
            "error": error
        }