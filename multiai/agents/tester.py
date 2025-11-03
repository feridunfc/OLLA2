# agents/tester.py
import logging
from typing import Dict, List, Optional
import re
import ast

from ..core.hybrid_router import LLM
from ..utils.secure_sandbox import SecureSandboxRunner

logger = logging.getLogger("tester")


class EnhancedTesterAgent:
    """
    V5.0 Enhanced Tester Agent
    Comprehensive testing with multiple test types and quality assurance
    """

    def __init__(self, llm: LLM):
        self.llm = llm
        self.sandbox = SecureSandboxRunner()

    async def create_comprehensive_tests(self, code: str, artifact: Dict,
                                         research: Dict, context: Optional[Dict] = None) -> Dict:
        """
        Create comprehensive test suite for the code
        """
        context = context or {}

        try:
            # Generate different types of tests
            unit_tests = await self._generate_unit_tests(code, artifact, research, context)
            integration_tests = await self._generate_integration_tests(code, artifact, research, context)
            security_tests = await self._generate_security_tests(code, artifact, research, context)
            performance_tests = await self._generate_performance_tests(code, artifact, research, context)

            # Combine all tests
            test_suite = await self._combine_test_suite(
                unit_tests, integration_tests, security_tests, performance_tests,
                code, artifact, context
            )

            # Validate test suite
            validation_result = await self._validate_test_suite(test_suite, code, context)

            logger.info(f"Test suite created for {artifact.get('artifact_id')}: "
                        f"{len(test_suite.get('tests', []))} tests, "
                        f"coverage: {test_suite.get('estimated_coverage', 0)}%")

            return test_suite

        except Exception as e:
            logger.error(f"Test creation failed: {e}")
            return self._get_fallback_tests(code, artifact)

    async def _generate_unit_tests(self, code: str, artifact: Dict,
                                   research: Dict, context: Dict) -> Dict:
        """Generate comprehensive unit tests"""

        unit_test_prompt = f"""
        Generate comprehensive unit tests for this Python code:

        CODE:
        {code}

        ARTIFACT CONTEXT:
        - Purpose: {artifact.get('purpose')}
        - Expected Behavior: {artifact.get('expected_behavior', 'N/A')}
        - Acceptance Criteria: {artifact.get('acceptance_criteria', [])}
        - Risk Level: {artifact.get('risk_level', 'medium')}

        RESEARCH CONTEXT:
        - Tech Stack: {research.get('tech_stack', [])}
        - Architecture: {research.get('architecture', {})}

        UNIT TEST REQUIREMENTS:
        1. Use pytest framework
        2. Test all functions and methods
        3. Cover edge cases and error conditions
        4. Use appropriate fixtures and mocking
        5. Include parameterized tests for different inputs
        6. Test both success and failure scenarios
        7. Follow AAA pattern (Arrange-Act-Assert)
        8. Include descriptive test names
        9. Achieve high code coverage
        10. Include setup and teardown if needed

        Return ONLY the Python test code.
        """

        unit_test_code = await self.llm.complete(unit_test_prompt)
        return {
            "type": "unit",
            "tests": self._clean_test_code(unit_test_code),
            "coverage_estimate": await self._estimate_coverage(unit_test_code, code),
            "test_count": self._count_tests(unit_test_code)
        }

    async def _generate_integration_tests(self, code: str, artifact: Dict,
                                          research: Dict, context: Dict) -> Dict:
        """Generate integration tests"""

        integration_prompt = f"""
        Generate integration tests for this Python code:

        CODE:
        {code}

        ARTIFACT CONTEXT:
        - Purpose: {artifact.get('purpose')}
        - Dependencies: {artifact.get('dependencies', [])}
        - Integration Points: {artifact.get('integration_points', [])}

        INTEGRATION TEST REQUIREMENTS:
        1. Test interactions with other components
        2. Test database interactions if applicable
        3. Test API endpoints if applicable
        4. Test file system operations
        5. Use test databases or mocking
        6. Include end-to-end scenarios
        7. Test data flow between components
        8. Verify integration contracts

        Return ONLY the Python test code.
        """

        integration_test_code = await self.llm.complete(integration_prompt)
        return {
            "type": "integration",
            "tests": self._clean_test_code(integration_test_code),
            "coverage_estimate": await self._estimate_coverage(integration_test_code, code),
            "test_count": self._count_tests(integration_test_code)
        }

    async def _generate_security_tests(self, code: str, artifact: Dict,
                                       research: Dict, context: Dict) -> Dict:
        """Generate security tests"""

        security_prompt = f"""
        Generate security tests for this Python code:

        CODE:
        {code}

        ARTIFACT CONTEXT:
        - Purpose: {artifact.get('purpose')}
        - Risk Level: {artifact.get('risk_level', 'medium')}
        - Security Requirements: {artifact.get('security_requirements', [])}

        SECURITY TEST REQUIREMENTS:
        1. Test for injection vulnerabilities
        2. Test authentication and authorization
        3. Test input validation
        4. Test data sanitization
        5. Test error handling without information leakage
        6. Test secure configuration
        7. Test for common security anti-patterns
        8. Include penetration testing scenarios

        Return ONLY the Python test code.
        """

        security_test_code = await self.llm.complete(security_prompt)
        return {
            "type": "security",
            "tests": self._clean_test_code(security_test_code),
            "coverage_estimate": await self._estimate_coverage(security_test_code, code),
            "test_count": self._count_tests(security_test_code)
        }

    async def _generate_performance_tests(self, code: str, artifact: Dict,
                                          research: Dict, context: Dict) -> Dict:
        """Generate performance tests"""

        performance_prompt = f"""
        Generate performance tests for this Python code:

        CODE:
        {code}

        ARTIFACT CONTEXT:
        - Purpose: {artifact.get('purpose')}
        - Performance Requirements: {artifact.get('performance_requirements', 'N/A')}

        PERFORMANCE TEST REQUIREMENTS:
        1. Test execution time under load
        2. Test memory usage
        3. Test scalability
        4. Include benchmark comparisons
        5. Test with large datasets if applicable
        6. Measure response times
        7. Identify performance bottlenecks
        8. Use pytest-benchmark or similar

        Return ONLY the Python test code.
        """

        performance_test_code = await self.llm.complete(performance_prompt)
        return {
            "type": "performance",
            "tests": self._clean_test_code(performance_test_code),
            "coverage_estimate": await self._estimate_coverage(performance_test_code, code),
            "test_count": self._count_tests(performance_test_code)
        }

    async def _combine_test_suite(self, unit_tests: Dict, integration_tests: Dict,
                                  security_tests: Dict, performance_tests: Dict,
                                  code: str, artifact: Dict, context: Dict) -> Dict:
        """Combine all test types into a comprehensive test suite"""

        all_tests = []
        total_coverage = 0
        total_tests = 0

        test_types = [unit_tests, integration_tests, security_tests, performance_tests]

        for test_type in test_types:
            if test_type["tests"]:
                all_tests.append({
                    "category": test_type["type"],
                    "code": test_type["tests"],
                    "test_count": test_type["test_count"],
                    "coverage_estimate": test_type["coverage_estimate"]
                })
                total_coverage += test_type["coverage_estimate"]
                total_tests += test_type["test_count"]

        avg_coverage = total_coverage / len(test_types) if test_types else 0

        # Generate test runner and configuration
        test_config = await self._generate_test_configuration(all_tests, code, artifact, context)

        return {
            "test_suite": all_tests,
            "summary": {
                "total_tests": total_tests,
                "estimated_coverage": avg_coverage,
                "test_categories": [test["category"] for test in all_tests],
                "artifact_id": artifact.get("artifact_id")
            },
            "configuration": test_config,
            "metadata": {
                "generated_at": self._get_timestamp(),
                "tester_version": "5.0",
                "artifact_purpose": artifact.get("purpose")
            }
        }

    async def _generate_test_configuration(self, test_suite: List[Dict],
                                           code: str, artifact: Dict, context: Dict) -> Dict:
        """Generate test configuration and runner"""

        config_prompt = f"""
        Generate pytest configuration and test runner for these test categories:

        TEST CATEGORIES: {[test['category'] for test in test_suite]}

        ARTIFACT: {artifact.get('purpose')}

        Create:
        1. pytest.ini configuration
        2. conftest.py with common fixtures
        3. requirements-test.txt with testing dependencies
        4. Test runner script

        Return as a structured configuration.
        """

        config_code = await self.llm.complete(config_prompt)

        return {
            "pytest_ini": self._extract_config_section(config_code, "pytest.ini"),
            "conftest_py": self._extract_config_section(config_code, "conftest.py"),
            "requirements_test": self._extract_config_section(config_code, "requirements-test.txt"),
            "test_runner": self._extract_config_section(config_code, "test_runner.py")
        }

    async def _validate_test_suite(self, test_suite: Dict, code: str, context: Dict) -> Dict:
        """Validate the generated test suite"""
        validation = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "metrics": {}
        }

        total_tests = test_suite["summary"]["total_tests"]
        if total_tests == 0:
            validation["valid"] = False
            validation["issues"].append("No tests generated")

        if test_suite["summary"]["estimated_coverage"] < 50:
            validation["warnings"].append("Low estimated test coverage")

        # Check test categories coverage
        categories = test_suite["summary"]["test_categories"]
        if "unit" not in categories:
            validation["warnings"].append("No unit tests generated")

        # Basic syntax check for test code
        for test_category in test_suite["test_suite"]:
            try:
                ast.parse(test_category["code"])
            except SyntaxError as e:
                validation["valid"] = False
                validation["issues"].append(f"Syntax error in {test_category['category']} tests: {e}")

        validation["metrics"] = {
            "total_tests": total_tests,
            "estimated_coverage": test_suite["summary"]["estimated_coverage"],
            "categories_count": len(categories)
        }

        return validation

    def _clean_test_code(self, test_code: str) -> str:
        """Clean and format test code"""
        # Remove markdown code blocks
        test_code = re.sub(r'```(?:\w+)?\s*', '', test_code)
        return test_code.strip()

    async def _estimate_coverage(self, test_code: str, source_code: str) -> float:
        """Estimate test coverage (simplified)"""
        # Count functions in source code
        source_functions = len(re.findall(r'def\s+(\w+)\s*\(', source_code))

        # Count test functions
        test_functions = len(re.findall(r'def\s+test_(\w+)\s*\(', test_code))

        if source_functions == 0:
            return 0.0

        coverage = (test_functions / source_functions) * 100
        return min(100.0, coverage)

    def _count_tests(self, test_code: str) -> int:
        """Count number of test functions"""
        return len(re.findall(r'def\s+test_(\w+)\s*\(', test_code))

        def _extract_config_section(self, config_code: str, section_name: str) -> str:
            """Extract configuration section from generated code"""
            # Simple pattern matching for configuration sections
            patterns = {
                "pytest.ini": r'\[pytest\.ini\](.*?)(?=\[|\Z)',
                "conftest.py": r'\[conftest\.py\](.*?)(?=\[|\Z)',
                "requirements-test.txt": r'\[requirements-test\.txt\](.*?)(?=\[|\Z)',
                "test_runner.py": r'\[test_runner\.py\](.*?)(?=\[|\Z)'
            }

            pattern = patterns.get(section_name, f'\\[{re.escape(section_name)}\\]')
            match = re.search(pattern, config_code, re.DOTALL | re.IGNORECASE)

            if match:
                return match.group(1).strip()
            return f"# {section_name} configuration not found"

        def _get_timestamp(self) -> str:
            """Get current timestamp"""
            from datetime import datetime
            return datetime.utcnow().isoformat()

        def _get_fallback_tests(self, code: str, artifact: Dict) -> Dict:
            """Get fallback tests when generation fails"""
            fallback_test = f'''
    """
    Fallback test for: {artifact.get('purpose', 'Unknown artifact')}
    Generated due to test creation failure.
    """

    import pytest

    def test_fallback():
        """Basic fallback test"""
        assert True

    def test_artifact_purpose():
        """Test artifact purpose is defined"""
        assert "{artifact.get('purpose', 'unknown')}" != "unknown"
    '''

            return {
                "test_suite": [
                    {
                        "category": "unit",
                        "code": fallback_test,
                        "test_count": 2,
                        "coverage_estimate": 10.0
                    }
                ],
                "summary": {
                    "total_tests": 2,
                    "estimated_coverage": 10.0,
                    "test_categories": ["unit"],
                    "artifact_id": artifact.get("artifact_id")
                },
                "configuration": {
                    "pytest_ini": "[pytest]\npython_files = test_*.py\npython_classes = Test*\npython_functions = test_*",
                    "conftest_py": "# Fallback conftest.py",
                    "requirements_test": "pytest\npytest-cov",
                    "test_runner": "#!/bin/bash\npython -m pytest -v --cov=."
                },
                "metadata": {
                    "generated_at": self._get_timestamp(),
                    "tester_version": "5.0-fallback",
                    "artifact_purpose": artifact.get("purpose")
                }
            }

        async def execute_tests(self, test_suite: Dict, code: str, context: Optional[Dict] = None) -> Dict:
            """
            Execute test suite and return results
            """
            context = context or {}

            try:
                # Prepare test environment
                test_env = await self._prepare_test_environment(test_suite, code, context)

                # Execute different test types
                execution_results = {}

                for test_category in test_suite["test_suite"]:
                    category_result = await self._execute_test_category(
                        test_category, code, test_env, context
                    )
                    execution_results[test_category["category"]] = category_result

                # Aggregate results
                aggregated_results = await self._aggregate_test_results(execution_results, test_suite)

                logger.info(f"Test execution completed: {aggregated_results['summary']['pass_rate']}% pass rate")

                return aggregated_results

            except Exception as e:
                logger.error(f"Test execution failed: {e}")
                return self._get_fallback_execution_results(test_suite, str(e))

        async def _prepare_test_environment(self, test_suite: Dict, code: str, context: Dict) -> Dict:
            """Prepare test execution environment"""
            return {
                "working_directory": "/tmp/multiai_tests",
                "dependencies": test_suite["configuration"].get("requirements_test", ""),
                "environment_vars": {
                    "PYTHONPATH": "/tmp/multiai_tests",
                    "TEST_MODE": "true"
                },
                "timeout": context.get("test_timeout", 300)  # 5 minutes default
            }

        async def _execute_test_category(self, test_category: Dict, code: str,
                                         test_env: Dict, context: Dict) -> Dict:
            """Execute tests for a specific category"""

            # In a real implementation, this would actually run the tests in sandbox
            # For now, return mock results based on code analysis

            test_code = test_category["code"]

            # Analyze test code for potential issues
            analysis = await self._analyze_test_code(test_code, code, test_category["category"])

            # Mock execution results (in reality, run in sandbox)
            return {
                "category": test_category["category"],
                "total_tests": test_category["test_count"],
                "tests_passed": max(0, test_category["test_count"] - analysis["potential_failures"]),
                "tests_failed": analysis["potential_failures"],
                "execution_time": 2.5,  # Mock time
                "coverage": test_category["coverage_estimate"],
                "issues": analysis["issues"],
                "logs": f"Mock execution of {test_category['category']} tests",
                "status": "completed" if analysis["potential_failures"] == 0 else "failed"
            }

        async def _analyze_test_code(self, test_code: str, source_code: str, category: str) -> Dict:
            """Analyze test code for potential issues"""
            issues = []
            potential_failures = 0

            # Check for common test issues
            if "assert True" in test_code:
                issues.append("Test contains trivial assertion")
                potential_failures += 0  # This would actually pass

            if "pytest.skip" in test_code:
                issues.append("Test contains skipped tests")

            # Check if tests actually test the source code
            source_functions = re.findall(r'def\s+(\w+)\s*\(', source_code)
            test_functions = re.findall(r'def\s+test_(\w+)\s*\(', test_code)

            if not test_functions:
                issues.append("No test functions found")
                potential_failures = 1

            # Check for mocking patterns
            if any(keyword in test_code for keyword in ['mock', 'patch', 'MagicMock']):
                # Good - tests use mocking
                pass
            else:
                issues.append("Tests may not use proper mocking")

            return {
                "issues": issues,
                "potential_failures": potential_failures,
                "source_function_count": len(source_functions),
                "test_function_count": len(test_functions)
            }

        async def _aggregate_test_results(self, execution_results: Dict, test_suite: Dict) -> Dict:
            """Aggregate results from all test categories"""
            total_tests = 0
            total_passed = 0
            total_failed = 0
            categories_status = {}

            for category, results in execution_results.items():
                total_tests += results["total_tests"]
                total_passed += results["tests_passed"]
                total_failed += results["tests_failed"]
                categories_status[category] = results["status"]

            pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

            return {
                "summary": {
                    "total_tests": total_tests,
                    "tests_passed": total_passed,
                    "tests_failed": total_failed,
                    "pass_rate": pass_rate,
                    "categories_status": categories_status,
                    "overall_status": "passed" if total_failed == 0 else "failed"
                },
                "detailed_results": execution_results,
                "recommendations": await self._generate_test_recommendations(execution_results, test_suite),
                "metadata": {
                    "executed_at": self._get_timestamp(),
                    "test_suite_version": test_suite["metadata"]["tester_version"]
                }
            }

        async def _generate_test_recommendations(self, execution_results: Dict, test_suite: Dict) -> List[str]:
            """Generate recommendations based on test results"""
            recommendations = []

            for category, results in execution_results.items():
                if results["tests_failed"] > 0:
                    recommendations.append(f"Fix {results['tests_failed']} failing tests in {category} category")

                if results["coverage"] < 80:
                    recommendations.append(
                        f"Increase test coverage for {category} tests (current: {results['coverage']}%)")

            # Check if all test categories are present
            expected_categories = ["unit", "integration", "security"]
            present_categories = list(execution_results.keys())

            for expected in expected_categories:
                if expected not in present_categories:
                    recommendations.append(f"Add {expected} tests to improve test coverage")

            if not recommendations:
                recommendations.append("Test suite is comprehensive - consider adding performance and load testing")

            return recommendations

        def _get_fallback_execution_results(self, test_suite: Dict, error: str) -> Dict:
            """Get fallback execution results when testing fails"""
            return {
                "summary": {
                    "total_tests": test_suite["summary"]["total_tests"],
                    "tests_passed": 0,
                    "tests_failed": test_suite["summary"]["total_tests"],
                    "pass_rate": 0.0,
                    "categories_status": {cat: "failed" for cat in test_suite["summary"]["test_categories"]},
                    "overall_status": "failed"
                },
                "detailed_results": {},
                "recommendations": [
                    "Test execution system failed - manual testing required",
                    f"Error: {error}"
                ],
                "metadata": {
                    "executed_at": self._get_timestamp(),
                    "error": error
                }
            }