# Sprint B — Secure Sandbox using Docker
import docker, os, uuid
from typing import Dict, Any

DEFAULT_IMAGE = "python:3.11-slim"

class SecureSandboxDocker:
    def __init__(self, image: str = DEFAULT_IMAGE):
        self.client = docker.from_env()
        self.image = image

    def run(self, cmd: str, mounts: Dict[str, str], timeout: int = 60) -> Dict[str, Any]:
        binds = {os.path.abspath(h): {"bind": c, "mode": "rw"} for h, c in mounts.items()}
        cfg = self.client.api.create_host_config(
            network_mode="none",
            readonly_rootfs=True,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges:true"],
            tmpfs={"/tmp": "rw,noexec,nosuid,size=100m"},
            mem_limit="512m",
            pids_limit=256,
        )
        name = f"multiai_{uuid.uuid4().hex[:8]}"
        container = self.client.api.create_container(
            image=self.image,
            command=["/bin/bash", "-lc", cmd],
            name=name,
            host_config=cfg,
            working_dir="/workspace",
        )
        try:
            self.client.api.start(container.get("Id"))
            rc = self.client.api.wait(container.get("Id"), timeout=timeout).get("StatusCode", 1)
            logs = self.client.api.logs(container.get("Id")).decode(errors="ignore")
            return {"ok": rc == 0, "stdout": logs}
        finally:
            self.client.api.remove_container(container.get("Id"), force=True)
