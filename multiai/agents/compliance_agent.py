# multiai/agents/compliance_agent.py
from __future__ import annotations
import re
import json
import logging
import ast
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..core.policy_agent import policy_agent

logger = logging.getLogger("compliance")


class ComplianceStandard(Enum):
    GDPR = "gdpr"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    CUSTOM = "custom"


class ViolationSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceViolation:
    """Uyumluluk ihlali detayları"""
    standard: ComplianceStandard
    rule_id: str
    description: str
    severity: ViolationSeverity
    location: str  # file:line or code section
    evidence: str
    mitigation: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ComplianceResult:
    """Uyumluluk kontrol sonucu"""
    compliant: bool
    score: float  # 0-100
    violations: List[ComplianceViolation]
    warnings: List[str]
    checked_standards: List[ComplianceStandard]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class EnhancedComplianceAgent:
    """
    V5.0 Enhanced Compliance Agent
    Gelişmiş uyumluluk denetimi ve güvenlik analizi
    """

    def __init__(self, policy_agent_instance=None):
        self.policy_agent = policy_agent_instance or policy_agent
        self.violations: List[ComplianceViolation] = []
        self.compliance_history: List[ComplianceResult] = []

        # Gelişmiş kurallar seti
        self.compliance_rules = self._initialize_compliance_rules()

        # Custom rules from policy
        self.custom_rules = self.policy_agent.security_policy.allowed_commands

        logger.info("ComplianceAgent initialized with enhanced rule set")

    def _initialize_compliance_rules(self) -> Dict[ComplianceStandard, List[Dict]]:
        """Gelişmiş uyumluluk kurallarını başlat"""

        return {
            ComplianceStandard.GDPR: [
                {
                    "id": "GDPR-001",
                    "pattern": r'\bpersonal_data\b|\buser_data\b|\bcustomer_data\b',
                    "description": "Personal data handling without proper consent",
                    "severity": ViolationSeverity.HIGH,
                    "mitigation": "Implement explicit consent mechanisms and data anonymization"
                },
                {
                    "id": "GDPR-002",
                    "pattern": r'\bemail\b.*\bstore\b|\bphone\b.*\bsave\b',
                    "description": "Storing contact information without encryption",
                    "severity": ViolationSeverity.MEDIUM,
                    "mitigation": "Encrypt personally identifiable information at rest"
                },
                {
                    "id": "GDPR-003",
                    "pattern": r'\bdelete\b.*\buser\b.*\bdata\b',
                    "description": "Missing data deletion functionality",
                    "severity": ViolationSeverity.MEDIUM,
                    "mitigation": "Implement right to be forgotten functionality"
                }
            ],

            ComplianceStandard.SOC2: [
                {
                    "id": "SOC2-001",
                    "pattern": r'subprocess\.run.*shell=True|os\.system|os\.popen',
                    "description": "Unsafe command execution",
                    "severity": ViolationSeverity.CRITICAL,
                    "mitigation": "Use secure subprocess with validated inputs"
                },
                {
                    "id": "SOC2-002",
                    "pattern": r'open\(.*/etc/passwd|open\(.*/etc/shadow',
                    "description": "Access to system files",
                    "severity": ViolationSeverity.CRITICAL,
                    "mitigation": "Remove unnecessary system file access"
                },
                {
                    "id": "SOC2-003",
                    "pattern": r'eval\(|exec\(|compile\(',
                    "description": "Dynamic code execution",
                    "severity": ViolationSeverity.HIGH,
                    "mitigation": "Avoid dynamic code execution or use strict sandboxing"
                },
                {
                    "id": "SOC2-004",
                    "pattern": r'password\s*=\s*["\'][^"\']+["\']|api_key\s*=',
                    "description": "Hardcoded credentials",
                    "severity": ViolationSeverity.HIGH,
                    "mitigation": "Use environment variables or secure secret management"
                }
            ],

            ComplianceStandard.ISO27001: [
                {
                    "id": "ISO27001-001",
                    "pattern": r'logging\.(info|debug|error).*(password|secret|key)',
                    "description": "Sensitive data in logs",
                    "severity": ViolationSeverity.HIGH,
                    "mitigation": "Implement log sanitization and avoid logging secrets"
                },
                {
                    "id": "ISO27001-002",
                    "pattern": r'http://[^\s]+|ftp://[^\s]+',
                    "description": "Unencrypted network communication",
                    "severity": ViolationSeverity.MEDIUM,
                    "mitigation": "Use HTTPS/FTPS for all network communications"
                },
                {
                    "id": "ISO27001-003",
                    "pattern": r'cryptography|encryption',
                    "description": "Missing or weak encryption",
                    "severity": ViolationSeverity.MEDIUM,
                    "mitigation": "Review and strengthen encryption implementation"
                }
            ],

            ComplianceStandard.HIPAA: [
                {
                    "id": "HIPAA-001",
                    "pattern": r'\bmedical\b|\bhealth\b|\bpatient\b|\bphi\b',
                    "description": "Healthcare data handling",
                    "severity": ViolationSeverity.HIGH,
                    "mitigation": "Implement HIPAA-compliant data protection measures"
                }
            ],

            ComplianceStandard.PCI_DSS: [
                {
                    "id": "PCI-DSS-001",
                    "pattern": r'credit_card|payment_card|pci',
                    "description": "Payment card data handling",
                    "severity": ViolationSeverity.HIGH,
                    "mitigation": "Implement PCI DSS compliant payment processing"
                }
            ]
        }

    async def analyze_code_comprehensive(self, code: str, context: Optional[Dict[str, Any]] = None) -> ComplianceResult:
        """
        Kapsamlı kod analizi ve uyumluluk denetimi
        """
        context = context or {}
        self.violations.clear()

        try:
            # Standartları belirle
            standards_to_check = await self._determine_applicable_standards(context)

            # Çok katmanlı analiz
            await self._perform_pattern_analysis(code, standards_to_check, context)
            await self._perform_ast_analysis(code, standards_to_check, context)
            await self._perform_security_analysis(code, context)

            # Sonuçları değerlendir
            compliance_result = self._evaluate_compliance(standards_to_check)

            # Geçmişe kaydet
            self.compliance_history.append(compliance_result)

            logger.info(
                f"Compliance analysis completed: {compliance_result.score}/100 - {len(compliance_result.violations)} violations")

            return compliance_result

        except Exception as e:
            logger.error(f"Compliance analysis failed: {e}")
            return self._create_error_result(str(e))

    async def _determine_applicable_standards(self, context: Dict[str, Any]) -> List[ComplianceStandard]:
        """Uygulanabilir uyumluluk standartlarını belirle"""
        standards = set()

        # Context'ten standartları al
        context_standards = context.get("compliance_requirements", [])
        for std in context_standards:
            try:
                standards.add(ComplianceStandard(std.lower()))
            except ValueError:
                logger.warning(f"Unknown compliance standard: {std}")

        # Policy'den standartları al
        if hasattr(self.policy_agent, 'compliance_requirements'):
            policy_standards = getattr(self.policy_agent.compliance_requirements, [])
            for std in policy_standards:
                try:
                    standards.add(ComplianceStandard(std.lower()))
                except ValueError:
                    logger.warning(f"Unknown compliance standard in policy: {std}")

        # Varsayılan standartlar
        if not standards:
            standards = {ComplianceStandard.SOC2, ComplianceStandard.ISO27001}

        return list(standards)

    async def _perform_pattern_analysis(self, code: str, standards: List[ComplianceStandard], context: Dict):
        """Pattern-based uyumluluk analizi"""

        for standard in standards:
            if standard not in self.compliance_rules:
                continue

            for rule in self.compliance_rules[standard]:
                matches = re.finditer(rule["pattern"], code, re.IGNORECASE | re.MULTILINE)

                for match in matches:
                    violation = ComplianceViolation(
                        standard=standard,
                        rule_id=rule["id"],
                        description=rule["description"],
                        severity=rule["severity"],
                        location=f"line:{self._get_line_number(code, match.start())}",
                        evidence=match.group(0),
                        mitigation=rule["mitigation"]
                    )
                    self.violations.append(violation)

    async def _perform_ast_analysis(self, code: str, standards: List[ComplianceStandard], context: Dict):
        """AST-based derin kod analizi"""
        try:
            tree = ast.parse(code)

            # AST visitor ile kod analizi
            analyzer = SecurityASTAnalyzer(standards)
            analyzer.visit(tree)
            self.violations.extend(analyzer.violations)

        except SyntaxError as e:
            logger.warning(f"AST analysis failed due to syntax error: {e}")
            self.violations.append(
                ComplianceViolation(
                    standard=ComplianceStandard.SOC2,
                    rule_id="SYNTAX-ERROR",
                    description="Code contains syntax errors",
                    severity=ViolationSeverity.MEDIUM,
                    location="global",
                    evidence=str(e),
                    mitigation="Fix syntax errors before compliance analysis"
                )
            )

    async def _perform_security_analysis(self, code: str, context: Dict):
        """Güvenlik odaklı ek analizler"""

        # Input validation kontrolü
        if any(pattern in code for pattern in ['input()', 'sys.argv', 'getpass']):
            if not any(pattern in code for pattern in ['validation', 'sanitize', 'escape']):
                self.violations.append(
                    ComplianceViolation(
                        standard=ComplianceStandard.SOC2,
                        rule_id="SEC-001",
                        description="Missing input validation",
                        severity=ViolationSeverity.HIGH,
                        location="global",
                        evidence="User input handling without validation",
                        mitigation="Implement input validation and sanitization"
                    )
                )

        # Error handling kontrolü
        if 'try:' not in code and 'except' not in code:
            has_risky_operations = any(op in code for op in ['open(', 'requests.get', 'subprocess.'])
            if has_risky_operations:
                self.violations.append(
                    ComplianceViolation(
                        standard=ComplianceStandard.ISO27001,
                        rule_id="SEC-002",
                        description="Missing error handling for risky operations",
                        severity=ViolationSeverity.MEDIUM,
                        location="global",
                        evidence="Risky operations without error handling",
                        mitigation="Add proper try-except blocks for error handling"
                    )
                )

    def _evaluate_compliance(self, standards: List[ComplianceStandard]) -> ComplianceResult:
        """Uyumluluk sonuçlarını değerlendir"""

        # Şiddet bazlı puanlama
        severity_weights = {
            ViolationSeverity.LOW: 1,
            ViolationSeverity.MEDIUM: 3,
            ViolationSeverity.HIGH: 7,
            ViolationSeverity.CRITICAL: 10
        }

        total_weight = sum(severity_weights.values())
        violation_weight = sum(severity_weights[v.severity] for v in self.violations)

        # Puan hesapla (0-100)
        compliance_score = max(0, 100 - (violation_weight / total_weight * 100))

        # Uyarılar
        warnings = []
        if any(v.severity == ViolationSeverity.CRITICAL for v in self.violations):
            warnings.append("Critical violations detected - immediate action required")

        if compliance_score < 70:
            warnings.append("Low compliance score - review and address violations")

        return ComplianceResult(
            compliant=compliance_score >= 80,  # %80 ve üstü compliant
            score=compliance_score,
            violations=self.violations.copy(),
            warnings=warnings,
            checked_standards=standards
        )

    async def analyze_critic_report(self, critic_report: Dict[str, Any]) -> ComplianceResult:
        """
        Critic agent raporunu uyumluluk açısından analiz et
        """
        context = {
            "compliance_requirements": critic_report.get("compliance_requirements", []),
            "artifact_type": critic_report.get("artifact_type", "code"),
            "risk_level": critic_report.get("risk_level", "medium")
        }

        code = critic_report.get("code", "")
        analysis_context = critic_report.get("analysis_context", {})

        # Critic'in güvenlik bulgularını işle
        security_issues = critic_report.get("security_issues", [])
        for issue in security_issues:
            self.violations.append(
                ComplianceViolation(
                    standard=ComplianceStandard.SOC2,
                    rule_id="CRITIC-SEC",
                    description=f"Security issue identified by critic: {issue}",
                    severity=ViolationSeverity.HIGH,
                    location="critic_analysis",
                    evidence=issue,
                    mitigation="Address security issues identified by critic agent"
                )
            )

        return await self.analyze_code_comprehensive(code, {**context, **analysis_context})

    def _get_line_number(self, code: str, position: int) -> int:
        """Pozisyona göre satır numarasını bul"""
        return code[:position].count('\n') + 1

    def _create_error_result(self, error: str) -> ComplianceResult:
        """Hata durumu için sonuç oluştur"""
        return ComplianceResult(
            compliant=False,
            score=0,
            violations=[],
            warnings=[f"Compliance analysis failed: {error}"],
            checked_standards=[]
        )

    def get_compliance_summary(self) -> Dict[str, Any]:
        """Uyumluluk durumu özeti"""
        if not self.compliance_history:
            return {"status": "no_analysis_performed"}

        latest_result = self.compliance_history[-1]

        # İstatistikler
        violation_stats = {}
        for standard in ComplianceStandard:
            standard_violations = [v for v in latest_result.violations if v.standard == standard]
            violation_stats[standard.value] = len(standard_violations)

        return {
            "latest_analysis": {
                "timestamp": latest_result.timestamp,
                "compliant": latest_result.compliant,
                "score": latest_result.score,
                "total_violations": len(latest_result.violations),
                "violation_breakdown": violation_stats
            },
            "history": {
                "total_analyses": len(self.compliance_history),
                "average_score": sum(r.score for r in self.compliance_history) / len(self.compliance_history),
                "compliance_trend": self._calculate_compliance_trend()
            },
            "recommendations": self._generate_compliance_recommendations(latest_result)
        }

    def _calculate_compliance_trend(self) -> str:
        """Uyumluluk trendini hesapla"""
        if len(self.compliance_history) < 2:
            return "insufficient_data"

        recent_scores = [r.score for r in self.compliance_history[-5:]]  # Son 5 analiz
        if len(recent_scores) < 2:
            return "stable"

        trend = recent_scores[-1] - recent_scores[0]
        if trend > 5:
            return "improving"
        elif trend < -5:
            return "declining"
        else:
            return "stable"

    def _generate_compliance_recommendations(self, result: ComplianceResult) -> List[Dict[str, Any]]:
        """Uyumluluk iyileştirme önerileri"""
        recommendations = []

        # Kritik ihlalleri önceliklendir
        critical_violations = [v for v in result.violations if v.severity == ViolationSeverity.CRITICAL]
        if critical_violations:
            recommendations.append({
                "priority": "critical",
                "action": "address_critical_violations",
                "description": f"Address {len(critical_violations)} critical compliance violations",
                "violations": [v.rule_id for v in critical_violations]
            })

        # Standart bazlı öneriler
        for standard in result.checked_standards:
            standard_violations = [v for v in result.violations if v.standard == standard]
            if standard_violations:
                recommendations.append({
                    "priority": "high",
                    "action": f"improve_{standard.value}_compliance",
                    "description": f"Address {len(standard_violations)} {standard.value} violations",
                    "standard": standard.value
                })

        # Genel öneriler
        if result.score < 80:
            recommendations.append({
                "priority": "medium",
                "action": "general_compliance_improvement",
                "description": f"Improve overall compliance score from {result.score} to 80+",
                "suggestions": ["Review coding standards", "Implement security best practices",
                                "Add comprehensive testing"]
            })

        return recommendations

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Detaylı uyumluluk raporu"""
        latest_result = self.compliance_history[-1] if self.compliance_history else None

        if not latest_result:
            return {"error": "No compliance analysis available"}

        return {
            "executive_summary": {
                "overall_status": "COMPLIANT" if latest_result.compliant else "NON_COMPLIANT",
                "compliance_score": latest_result.score,
                "total_standards_checked": len(latest_result.checked_standards),
                "total_violations": len(latest_result.violations),
                "analysis_date": latest_result.timestamp
            },
            "detailed_analysis": {
                "violations_by_severity": self._group_violations_by_severity(latest_result.violations),
                "violations_by_standard": self._group_violations_by_standard(latest_result.violations),
                "checked_standards": [std.value for std in latest_result.checked_standards]
            },
            "improvement_plan": {
                "immediate_actions": [r for r in self._generate_compliance_recommendations(latest_result)
                                      if r["priority"] in ["critical", "high"]],
                "long_term_strategy": [
                    "Implement automated compliance testing in CI/CD",
                    "Provide developer training on compliance requirements",
                    "Establish compliance review process for all code changes"
                ]
            },
            "compliance_history": {
                "total_analyses": len(self.compliance_history),
                "average_score": sum(r.score for r in self.compliance_history) / len(self.compliance_history),
                "trend": self._calculate_compliance_trend()
            }
        }

    def _group_violations_by_severity(self, violations: List[ComplianceViolation]) -> Dict[str, int]:
        """İhlalleri şiddete göre grupla"""
        groups = {}
        for severity in ViolationSeverity:
            groups[severity.value] = len([v for v in violations if v.severity == severity])
        return groups

    def _group_violations_by_standard(self, violations: List[ComplianceViolation]) -> Dict[str, int]:
        """İhlalleri standarda göre grupla"""
        groups = {}
        for standard in ComplianceStandard:
            groups[standard.value] = len([v for v in violations if v.standard == standard])
        return groups

    def to_json(self) -> str:
        """JSON raporu"""
        return json.dumps(self.generate_compliance_report(), indent=2, default=str)


class SecurityASTAnalyzer(ast.NodeVisitor):
    """AST-based güvenlik analizörü"""

    def __init__(self, standards: List[ComplianceStandard]):
        self.standards = standards
        self.violations: List[ComplianceViolation] = []

    def visit_Call(self, node):
        """Fonksiyon çağrılarını analiz et"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id

            # Güvensiz fonksiyonlar
            unsafe_functions = {
                'eval': "Avoid eval() - use safer alternatives",
                'exec': "Avoid exec() - potential code injection",
                'input': "Use getpass or validated input instead",
            }

            if func_name in unsafe_functions:
                self.violations.append(
                    ComplianceViolation(
                        standard=ComplianceStandard.SOC2,
                        rule_id=f"AST-{func_name.upper()}",
                        description=f"Unsafe function call: {func_name}",
                        severity=ViolationSeverity.HIGH,
                        location=f"line:{node.lineno}",
                        evidence=func_name,
                        mitigation=unsafe_functions[func_name]
                    )
                )

        self.generic_visit(node)

    def visit_Assign(self, node):
        """Atama işlemlerini analiz et"""
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id

            # Hassas veri atamaları
            sensitive_patterns = {
                'password': "Use environment variables for passwords",
                'api_key': "Use secure secret management for API keys",
                'secret': "Avoid hardcoding secrets in source code"
            }

            for pattern, mitigation in sensitive_patterns.items():
                if pattern in var_name.lower():
                    self.violations.append(
                        ComplianceViolation(
                            standard=ComplianceStandard.ISO27001,
                            rule_id="AST-SENSITIVE-ASSIGN",
                            description=f"Potential sensitive data assignment: {var_name}",
                            severity=ViolationSeverity.MEDIUM,
                            location=f"line:{node.lineno}",
                            evidence=var_name,
                            mitigation=mitigation
                        )
                    )

        self.generic_visit(node)


# Global instance
compliance_agent = EnhancedComplianceAgent()