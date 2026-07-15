"""FastMCP surface: factory operations as MCP tools for agents."""
from __future__ import annotations

from utag_core.schemas.factory import JobKind
from utag_factory.runtime import connect


def build_server():
    from fastmcp import FastMCP

    mcp = FastMCP("utag-factory")
    rt = connect(worker_name="mcp")

    @mcp.tool
    def submit_run_python(script: str) -> dict:
        """Queue a sandboxed python script; returns the job id."""
        job = rt.worker("mcp").submit(JobKind.run_python, {"script": script})
        return {"job_id": job.id, "status": job.status.value}

    @mcp.tool
    def submit_generate(target: str, prompt_yaml: str) -> dict:
        """Queue a generate-artifact job for a registered generator target."""
        job = rt.worker("mcp").submit(
            JobKind.generate_artifact, {"target": target, "prompt_yaml": prompt_yaml})
        return {"job_id": job.id, "status": job.status.value}

    @mcp.tool
    def job_status(job_id: str) -> dict:
        """Current status of a job, with result if finished."""
        job = rt.store.get(job_id)
        try:
            result = rt.store.get_result(job_id)
        except KeyError:
            result = None
        return {"job_id": job.id, "status": job.status.value,
                "attempts": job.attempts, "result": result}

    @mcp.tool
    def queue_signals() -> dict:
        """Live queue depth / pending / oldest-age (the scaling signals)."""
        return {"depth": rt.queue.depth(), "pending": rt.queue.pending(),
                "oldest_job_age_s": rt.queue.oldest_job_age_s()}

    return mcp
