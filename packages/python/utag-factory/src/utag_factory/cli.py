"""Typer CLI: utag-factory — submit, work, supervise, serve, doctor."""
from __future__ import annotations

import json

import typer

from utag_core.schemas.factory import JobKind

app = typer.Typer(help="utag internal automation factory", no_args_is_help=True)


@app.command()
def doctor():
    """Validate the canonical template and report the resolved profile."""
    from utag_factory.config import load_config
    cfg = load_config()
    typer.echo(f"profile: {cfg.active_profile_name}  "
               f"workers=({cfg.worker_profile.min_workers},{cfg.worker_profile.max_workers})")
    typer.echo(f"supervisor: {cfg.profile.execution.supervisor}  "
               f"isolation: {cfg.profile.execution.default_isolation.value}")
    typer.echo(f"redis: {cfg.redis_url}")


@app.command()
def submit(script: str = typer.Option("", "--script"),
           target: str = typer.Option("", "--target"),
           prompt_file: str = typer.Option("", "--prompt-file"),
           nl: str = typer.Option("", "--nl", help="natural-language request (routed via agent)")):
    """Queue a job from a script, a generator target, or a natural-language ask."""
    from utag_factory.runtime import connect
    rt = connect(worker_name="cli")
    w = rt.worker("cli")
    if nl:
        from utag_factory.agent import plan_job
        req = plan_job(nl)
        job = w.submit(req.kind, req.to_payload())
        typer.echo(f"planned kind={req.kind.value}  job={job.id}")
    elif script:
        job = w.submit(JobKind.run_python, {"script": script})
        typer.echo(job.id)
    elif target and prompt_file:
        from pathlib import Path
        job = w.submit(JobKind.generate_artifact,
                       {"target": target, "prompt_yaml": Path(prompt_file).read_text()})
        typer.echo(job.id)
    else:
        raise typer.BadParameter("need --script, --target+--prompt-file, or --nl")


@app.command()
def work(name: str = typer.Option("worker-1", "--name"),
         once: bool = typer.Option(False, "--once")):
    """Run a worker: claim and execute jobs (daemon body)."""
    import time
    from utag_factory.runtime import connect
    rt = connect(worker_name=name)
    w = rt.worker(name)
    while True:
        job = w.run_once(block_ms=2000)
        if job is not None:
            typer.echo(f"{job.id} -> {job.status.value}")
        if once:
            break
        time.sleep(0.05)


@app.command()
def supervise(once: bool = typer.Option(False, "--once")):
    """Run the autoscaling supervisor loop."""
    import time
    from utag_factory.config import parse_duration_s
    from utag_factory.runtime import connect
    from utag_factory.supervisor import Supervisor
    rt = connect(worker_name="supervisor")
    sup = Supervisor(cfg=rt.cfg, queue=rt.queue)
    interval = parse_duration_s(rt.cfg.profile.scaling.poll_interval)
    while True:
        d = sup.reconcile()
        typer.echo(f"workers {d.current} -> {d.desired}  ({d.reason})")
        if once:
            break
        time.sleep(interval)


@app.command()
def status(job_id: str):
    """Print a job's record and result."""
    from utag_factory.runtime import connect
    rt = connect(worker_name="cli")
    job = rt.store.get(job_id)
    try:
        result = rt.store.get_result(job_id)
    except KeyError:
        result = None
    typer.echo(json.dumps({"status": job.status.value, "attempts": job.attempts,
                           "result": result}, indent=2))


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8770):
    """Serve the FastAPI job API + SSE event firehose."""
    import uvicorn
    from utag_factory.api import create_app
    uvicorn.run(create_app(), host=host, port=port)


@app.command()
def mcp():
    """Run the FastMCP server exposing factory tools to agents."""
    from utag_factory.mcp_server import build_server
    build_server().run()


if __name__ == "__main__":
    app()
