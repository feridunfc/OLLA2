import subprocess, logging
from typing import Dict, List, Any
log = logging.getLogger("bash")
SAFE_COMMANDS: dict[str, List[str]] = {
    "ls": ["-l", "-a"],
    "pwd": [], "cat": [], "mkdir": ["-p"], "grep": ["-n", "-r", "-i"]
}
class SecureBash:
    def __init__(self, cwd: str):
        import pathlib; self.cwd = str(pathlib.Path(cwd).resolve())
    def exec(self, command: str, args: List[str]) -> Dict[str, Any]:
        if command not in SAFE_COMMANDS: return {"error":"command_not_allowed","command":command}
        allowed = SAFE_COMMANDS[command]
        clean = [a for a in args if not a.startswith("-") or a in allowed]
        try:
            p = subprocess.run([command]+clean, cwd=self.cwd, capture_output=True, text=True, shell=False, timeout=30)
            return {"stdout": p.stdout, "stderr": p.stderr, "returncode": p.returncode, "cwd": self.cwd}
        except subprocess.TimeoutExpired: return {"error":"timeout"}
        except Exception as e: return {"error": str(e)}
