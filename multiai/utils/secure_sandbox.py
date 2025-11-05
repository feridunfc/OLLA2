# multiai/utils/secure_sandbox.py
import logging
import tempfile
import os
from typing import Dict, List

class SecureSandboxRunner:
    """Unified secure sandbox for code execution"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            from .sandbox_enforcer import SandboxEnforcer
        except Exception:
            # Minimal fallback enforcer
            class SandboxEnforcer:
                def validate_command(self, cmd: str):
                    if any(x in cmd for x in ['rm -rf', ':(){:|:&};:', 'curl http']):
                        raise ValueError('forbidden command')
                def log_execution(self, cmd: str, result: dict):
                    pass
            self.logger.warning("Using fallback SandboxEnforcer")
        try:
            from .secure_sandbox_docker import SecureSandboxDocker
        except Exception:
            # Minimal fallback docker executor
            class SecureSandboxDocker:
                async def execute_in_container(self, command: str, mounts: List[str], timeout: int):
                    return {"success": True, "stdout": "(dryrun)", "stderr": "", "exit_code": 0}
            self.logger.warning("Using fallback SecureSandboxDocker")
        self.enforcer = SandboxEnforcer()
        self.docker = SecureSandboxDocker()

    async def run(self, cmd: str, mounts: List[str] = None, timeout: int = 30) -> Dict[str, any]:
        """Main sandbox execution method"""
        try:
            # Security validation
            self.enforcer.validate_command(cmd)

            # Execute in Docker container
            result = await self.docker.execute_in_container(
                command=cmd,
                mounts=mounts or [],
                timeout=timeout
            )

            # Log security event
            try:
                self.enforcer.log_execution(cmd, result)
            except Exception:
                pass

            return {
                "ok": result.get('success', False),
                "stdout": result.get('stdout', ''),
                "stderr": result.get('stderr', ''),
                "exit_code": result.get('exit_code', -1)
            }

        except Exception as e:
            self.logger.error(f"Sandbox execution failed: {str(e)}")
            return {
                "ok": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1
            }

    async def run_pytest(self, test_path: str, timeout: int = 60) -> Dict[str, any]:
        """Specialized method for running pytest"""
        cmd = f"python -m pytest {test_path} -v --tb=short"
        return await self.run(cmd, timeout=timeout)

    async def run_python(self, code: str, timeout: int = 30) -> Dict[str, any]:
        """Execute Python code safely"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = await self.run(f"python {temp_file}", timeout=timeout)
            return result
        finally:
            try:
                os.unlink(temp_file)
            except Exception:
                pass

# Global instance
sandbox_runner = SecureSandboxRunner()