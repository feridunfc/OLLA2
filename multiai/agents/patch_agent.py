import logging, difflib, os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PatchAgent:
    """Generate unified diffs based on critic analysis."""
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_patch(self, critic_analysis: Dict[str, Any], original_code: str, modified_code: str, file_path: str="code.py") -> Dict[str, Any]:
        try:
            diff = self._unified_diff(original_code, modified_code, file_path)
            header = "# AUTO-PATCH (MULTIAI V5)\n" \
                     f"# impact={critic_analysis.get('impact','low')}, severity={critic_analysis.get('severity','low')}\n"
            content = header + diff
            fname = f"auto_patch_{os.path.basename(file_path)}.diff"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "patch_file": fname, "patch_content": content, "format": "unified_diff"}
        except Exception as e:
            logger.exception("patch generation failed")
            return {"status": "error", "error": str(e)}

    def _unified_diff(self, original: str, modified: str, file_path: str) -> str:
        a = original.splitlines(keepends=True)
        b = modified.splitlines(keepends=True)
        diff = difflib.unified_diff(a, b, fromfile=f"a/{file_path}", tofile=f"b/{file_path}", lineterm="")
        return "".join(diff)
