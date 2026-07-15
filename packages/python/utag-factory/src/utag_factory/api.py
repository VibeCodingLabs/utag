"""FastAPI surface: submit/inspect jobs + live SSE firehose over utag:events."""
from __future__ import annotations

import json
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utag_core.schemas.factory import JobKind, ResourceContract
from utag_factory.runtime import Runtime, connect


class SubmitRequest(BaseModel):
    kind: JobKind
    payload: dict
    resources: ResourceContract | None = None


def create_app(runtime: Runtime | None = None) -> FastAPI:
    app = FastAPI(title="utag-factory")
    rt = runtime or connect(worker_name="api")

    @app.get("/health")
    def health():
        return {"status": "ok", "profile": rt.cfg.active_profile_name,
                "queue_depth": rt.queue.depth()}

    @app.post("/jobs")
    def submit(req: SubmitRequest):
        job = rt.worker("api").submit(req.kind, req.payload, resources=req.resources)
        return {"job_id": job.id, "status": job.status.value}

    @app.get("/jobs/{job_id}")
    def get_job(job_id: str):
        try:
            job = rt.store.get(job_id)
        except KeyError:
            raise HTTPException(404, f"no job {job_id}") from None
        body = json.loads(job.model_dump_json(exclude_none=True))
        try:
            body["result"] = rt.store.get_result(job_id)
        except KeyError:
            body["result"] = None
        return body

    @app.get("/dlq")
    def dead_letters():
        return [json.loads(e.model_dump_json(exclude_none=True)) for e in rt.queue.dead_letters()]

    @app.get("/events")
    def events(last_id: str = "$", follow: bool = True):
        """SSE firehose over utag:events. follow=false drains what's buffered and
        stops (used by tests and one-shot tails); follow=true streams live."""
        return StreamingResponse(_event_stream(rt, last_id, follow=follow),
                                 media_type="text/event-stream")

    return app


def _event_stream(rt: Runtime, last_id: str, follow: bool):
    cursor = last_id
    while True:
        resp = rt.queue.r.xread({rt.cfg.streams.events: cursor},
                                block=1000 if follow else None, count=10)
        if not resp:
            if not follow:
                return
            yield ": keepalive\n\n"
            continue
        for _sname, messages in resp:
            for mid, fields in messages:
                cursor = mid.decode() if isinstance(mid, bytes) else mid
                data = {(k.decode() if isinstance(k, bytes) else k):
                        (v.decode() if isinstance(v, bytes) else v)
                        for k, v in fields.items()}
                yield f"id: {cursor}\ndata: {json.dumps(data)}\n\n"
