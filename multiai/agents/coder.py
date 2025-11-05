# agents/coder.py
import logging
from typing import Dict, List, Optional
import re

from ..core.hybrid_router import LLM
from ..core.policy_agent import policy_agent
from ..utils.secure_sandbox import SecureSandboxRunner

logger = logging.getLogger("coder")


class EnhancedCoderAgent:
    """
    V5.0 Enhanced Coder Agent - GERÇEK KOD ÜRETİMİ
    Advanced code generation with security, testing, and best practices
    """

    def __init__(self, llm: LLM):
        self.llm = llm
        self.policy_agent = policy_agent
        self.sandbox = SecureSandboxRunner()

    async def implement_artifact(self, artifact: Dict, research: Dict, context: Optional[Dict] = None) -> str:
        """
        Implement artifact with enhanced code generation
        """
        context = context or {}

        try:
            # Build comprehensive coding prompt
            coder_prompt = self._build_coder_prompt(artifact, research, context)

            # Generate code using hybrid router
            generated_code = await self.llm.complete(coder_prompt)

            # Clean and validate code
            cleaned_code = self._clean_generated_code(generated_code, artifact)

            # Apply security and best practices
            secured_code = await self._apply_security_checks(cleaned_code, artifact, context)

            # Generate accompanying tests
            test_code = await self._generate_tests(secured_code, artifact, research)

            # Validate code structure
            validation_result = await self._validate_code_structure(secured_code, artifact)

            if not validation_result["valid"]:
                logger.warning(f"Code validation failed: {validation_result['errors']}")
                # Attempt to fix validation issues
                secured_code = await self._fix_validation_issues(secured_code, validation_result["errors"])

            logger.info(f"Coder implemented artifact: {artifact.get('artifact_id')} - {len(secured_code)} chars")

            # Return main code with tests as separate if needed
            return self._format_final_output(secured_code, test_code, artifact)

        except Exception as e:
            logger.error(f"Coder implementation failed: {e}")
            return self._generate_fallback_code(artifact, research)

    def _build_coder_prompt(self, artifact: Dict, research: Dict, context: Dict) -> str:
        """Build comprehensive coding prompt"""

        artifact_type = artifact.get("type", "code")
        security_requirements = self.policy_agent.security_policy.allowed_commands

        return f"""
        As an AI Senior Software Engineer, implement this artifact:

        ARTIFACT DETAILS:
        - ID: {artifact.get('artifact_id')}
        - Type: {artifact_type}
        - Path: {artifact.get('path')}
        - Purpose: {artifact.get('purpose')}
        - Expected Behavior: {artifact.get('expected_behavior', 'N/A')}
        - Acceptance Criteria: {artifact.get('acceptance_criteria', [])}
        - Risk Level: {artifact.get('risk_level', 'medium')}

        RESEARCH CONTEXT:
        {self._format_research(research)}

        TECHNICAL REQUIREMENTS:
        - Tech Stack: {research.get('tech_stack', ['Python'])}
        - Architecture: {research.get('architecture_pattern', 'modular')}
        - Security: {security_requirements}

        CODING STANDARDS:
        1. Follow PEP 8 for Python code
        2. Include type hints
        3. Add docstrings for all functions/classes
        4. Implement proper error handling
        5. Use secure coding practices
        6. Include necessary imports
        7. Make code testable and modular

        SECURITY REQUIREMENTS:
        - Input validation for all external inputs
        - Safe file operations
        - No hardcoded secrets
        - Proper error handling without information leakage

        CONTEXT:
        - Collaboration Mode: {context.get('mode', 'full-auto')}
        - Compliance: {context.get('compliance', [])}

        Return ONLY the implementation code without explanations.
        Focus on production-ready, secure, and maintainable code.
        """

    async def _apply_security_checks(self, code: str, artifact: Dict, context: Dict) -> str:
        """Apply security checks and enhancements"""

        security_issues = self._scan_security_issues(code, artifact)

        if security_issues:
            logger.warning(f"Security issues found: {security_issues}")
            # Attempt to fix security issues
            fixed_code = await self._fix_security_issues(code, security_issues, artifact)
            return fixed_code

        return code

    def _scan_security_issues(self, code: str, artifact: Dict) -> List[str]:
        """Scan code for common security issues"""
        issues = []

        # Check for hardcoded secrets
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']'
        ]

        for pattern in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append("Hardcoded secret detected")

        # Check for unsafe eval/exec
        if 'eval(' in code or 'exec(' in code:
            issues.append("Unsafe eval/exec usage")

        # Check for SQL injection patterns
        if any(pattern in code for pattern in ['f"SELECT', 'f"INSERT', 'f"UPDATE', 'f"DELETE']):
            issues.append("Potential SQL injection vulnerability")

        return issues

    async def _fix_security_issues(self, code: str, issues: List[str], artifact: Dict) -> str:
        """Fix identified security issues"""
        security_fix_prompt = f"""
        Fix security issues in this code:

        CODE:
        {code}

        SECURITY ISSUES:
        {chr(10).join(issues)}

        ARTIFACT CONTEXT:
        - Purpose: {artifact.get('purpose')}
        - Type: {artifact.get('type')}

        Fix all security issues while maintaining functionality.
        Return ONLY the fixed code.
        """

        fixed_code = await self.llm.complete(security_fix_prompt)
        return self._clean_generated_code(fixed_code, artifact)

    async def _generate_tests(self, code: str, artifact: Dict, research: Dict) -> str:
        """Generate accompanying tests for the code"""

        if artifact.get("type") != "code":
            return ""

        test_prompt = f"""
        Generate comprehensive tests for this code:

        CODE:
        {code}

        ARTIFACT:
        - Purpose: {artifact.get('purpose')}
        - Expected Behavior: {artifact.get('expected_behavior', 'N/A')}
        - Acceptance Criteria: {artifact.get('acceptance_criteria', [])}

        TEST REQUIREMENTS:
        - Use pytest framework
        - Cover all functions and edge cases
        - Include integration tests if applicable
        - Mock external dependencies
        - Include error case testing

        Return ONLY the test code in Python.
        """

        test_code = await self.llm.complete(test_prompt)
        return self._clean_generated_code(test_code, artifact)

    async def _validate_code_structure(self, code: str, artifact: Dict) -> Dict:
        """Validate code structure and syntax"""
        # Basic validation - in production, you'd use AST parsing
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # Check for basic Python syntax
        if not code.strip():
            validation_result["valid"] = False
            validation_result["errors"].append("Empty code generated")

        # Check for required components based on artifact type
        if artifact.get("type") == "code":
            if "def " not in code and "class " not in code:
                validation_result["warnings"].append("No functions or classes found")

        return validation_result

    async def _fix_validation_issues(self, code: str, errors: List[str]) -> str:
        """Fix code validation issues"""
        if not errors:
            return code

        fix_prompt = f"""
        Fix validation issues in this code:

        CODE:
        {code}

        VALIDATION ERRORS:
        {chr(10).join(errors)}

        Return ONLY the fixed code.
        """

        fixed_code = await self.llm.complete(fix_prompt)
        return self._clean_generated_code(fixed_code, {"artifact_id": "validation_fix"})

    def _clean_generated_code(self, code: str, artifact: Dict) -> str:
        """Clean and format generated code"""
        # Remove markdown code blocks if present
        code = re.sub(r'```(?:\w+)?\s*', '', code)
        code = code.strip()

        # Ensure proper file extension based on artifact type
        artifact_type = artifact.get("type", "code")
        if artifact_type == "code" and artifact.get("path", "").endswith(".py"):
            # Ensure Python file starts properly
            if not code.startswith(('import ', 'from ', 'def ', 'class ', '"', "'", '#!')):
                code = f'"""\n{artifact.get("purpose", "Generated artifact")}\n"""\n\n{code}'

        return code

    def _format_research(self, research: Dict) -> str:
        """Format research data for prompt"""
        return "\n".join([
            f"- Tech Stack: {research.get('tech_stack', [])}",
            f"- Requirements: {research.get('requirements', [])}",
            f"- Risks: {research.get('risks', [])}",
            f"- Acceptance Criteria: {research.get('acceptance_criteria', [])}"
        ])

    def _format_final_output(self, main_code: str, test_code: str, artifact: Dict) -> str:
        """Format final code output"""
        if test_code and artifact.get("type") == "code":
            return f"{main_code}\n\n# TESTS\n{test_code}"
        return main_code

    def _generate_fallback_code(self, artifact: Dict, research: Dict) -> str:
        """Generate fallback code when AI fails"""
        artifact_type = artifact.get("type", "code")

        if artifact_type == "code":
            return f'''
"""
Fallback implementation for: {artifact.get("purpose", "Unknown artifact")}
This is a placeholder due to generation failure.
"""

def main():
    """Placeholder function"""
    print("Placeholder implementation")
    return None

if __name__ == "__main__":
    main()
'''
        else:
            return f"# Placeholder for {artifact_type}: {artifact.get('purpose')}"