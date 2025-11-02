import docker, os
def _get_client(): return docker.from_env()
def run_in_sandbox(cmd=("python","-c","print('ok')")):
    c=_get_client()
    cont=c.containers.run("python:3.11-slim",cmd,detach=True,network_mode="none",user="1000:1000",cap_drop=["ALL"],read_only=True)
    r=cont.wait(timeout=30)
    logs=cont.logs().decode(errors="ignore")
    cont.remove(force=True)
    return r,logs
