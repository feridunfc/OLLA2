import logging, hashlib, ast, re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CriticAgent:
    """
    Enhanced critic agent for code diff analysis and patch recommendations.
    analyze_diff(old_code, new_code) -> JSON
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_diff(self, old_code: str, new_code: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        try:
            old_hash = hashlib.sha256(old_code.encode("utf-8")).hexdigest()
            new_hash = hashlib.sha256(new_code.encode("utf-8")).hexdigest()

            security = self._analyze_security_changes(old_code, new_code)
            quality  = self._analyze_quality_changes(old_code, new_code)
            perf     = self._analyze_performance_changes(old_code, new_code)

            severity, impact = self._score(security, quality, perf)
            recommendations = self._recommend(security, quality, perf)

            return {
                "old_hash": old_hash,
                "new_hash": new_hash,
                "impact": impact,
                "severity": severity,
                "recommendations": recommendations,
                "security_issues": security,
                "quality_issues": quality,
                "performance_issues": perf,
                "approved": severity in ("low", "medium"),
                "requires_approval": severity in ("high", "critical"),
                "status": "success",
            }
        except Exception as e:
            logger.exception("critic analyze failed")
            return {
                "impact": "unknown",
                "severity": "high",
                "recommendations": ["Analysis failed - manual review required"],
                "approved": False,
                "requires_approval": True,
                "status": "error",
                "error": str(e),
            }

    def _analyze_security_changes(self, old_code: str, new_code: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        checks = [
            (r"eval\s*\(", "Use of eval()"),
            (r"exec\s*\(", "Use of exec()"),
            (r"subprocess\.[a-zA-Z_]*\(.*shell\s*=\s*True", "Subprocess shell=True"),
            (r"pickle\.loads", "Unsafe deserialization (pickle.loads)"),
            (r"password\s*=\s*['\"]", "Possible hardcoded password"),
            (r"token\s*=\s*['\"]", "Possible hardcoded token"),
            (r"key\s*=\s*['\"]", "Possible hardcoded key"),
        ]
        for pattern, msg in checks:
            if re.search(pattern, new_code, re.IGNORECASE) and not re.search(pattern, old_code, re.IGNORECASE):
                issues.append({"type": "security", "message": msg, "severity": "high"})
        return issues

    def _analyze_quality_changes(self, old_code: str, new_code: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        try:
            if new_code.strip():
                ast.parse(new_code)
        except SyntaxError as e:
            issues.append({"type": "syntax", "message": f"Syntax error: {e}", "severity": "high"})
        for i, line in enumerate(new_code.splitlines(), 1):
            if len(line) > 100:
                issues.append({"type": "style", "message": f"Line {i} >100 chars", "severity": "low"})
            if line.rstrip() != line:
                issues.append({"type": "style", "message": f"Line {i} trailing whitespace", "severity": "low"})
        return issues

    def _analyze_performance_changes(self, old_code: str, new_code: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        if re.search(r"for\s+.*:\s*\n\s*for\s+.*:", new_code):
            issues.append({"type": "performance", "message": "Nested loops detected", "severity": "medium"})
        return issues

    def _score(self, sec, qual, perf):
        levels = [i.get("severity", "low") for i in (sec + qual + perf)]
        if any(l == "critical" for l in levels): return "critical", "critical"
        if any(l == "high" for l in levels):     return "high", "high"
        if any(l == "medium" for l in levels):   return "medium", "medium"
        return "low", "low"

    def _recommend(self, sec, qual, perf):
        rec = []
        for i in sec:
            rec.append(f"SECURITY: {i['message']}")
        for i in qual:
            if i["type"] == "syntax":
                rec.append(f"FIX: {i['message']}")
            elif i["type"] == "style":
                rec.append(f"IMPROVE: {i['message']}")
        for i in perf:
            rec.append(f"PERFORMANCE: {i['message']}")
        return rec or ["No critical issues found"]
