import json, click, httpx
from .server.app import SprintRequest
@click.group()
def cli(): ...
@cli.command()
@click.option("--goal", required=True)
@click.option("--workdir", default="workspace")
@click.option("--mode", type=click.Choice(["local","cloud","auto"]), default="auto")
@click.option("--api", default="http://localhost:8084")
def sprint(goal, workdir, mode, api):
    req = SprintRequest(goal=goal, workdir=workdir, mode=mode)
    data = json.loads(req.model_dump_json())
    r = httpx.post(f"{api}/api/sprint/start", json=data, timeout=30.0)
    r.raise_for_status()
    click.echo(r.json())
if __name__ == "__main__":
    cli()
