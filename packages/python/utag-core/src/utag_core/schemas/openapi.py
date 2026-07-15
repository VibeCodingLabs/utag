"""OpenAPI pipeline contracts: normalized operation records and lint/diff reports."""
from __future__ import annotations

from enum import Enum

from pydantic import Field

from utag_core.schemas import SLUG, StrictSchema


class HttpMethod(str, Enum):
    get = "get"
    put = "put"
    post = "post"
    delete = "delete"
    options = "options"
    head = "head"
    patch = "patch"
    trace = "trace"


class OpenApiOperation(StrictSchema):
    operation_id: str = Field(min_length=1)
    method: HttpMethod
    path: str = Field(pattern=r"^/")
    summary: str = ""
    tags: list[str] = []
    has_request_schema: bool = False
    has_response_schema: bool = False


class OpenApiDiffEntry(StrictSchema):
    kind: str = Field(pattern=SLUG)  # added|removed|changed under a closed set at emit time
    pointer: str = Field(min_length=1)
    detail: str = ""


class OpenApiDiffReport(StrictSchema):
    old: str = Field(min_length=1)
    new: str = Field(min_length=1)
    entries: list[OpenApiDiffEntry] = []


class OpenApiReadinessReport(StrictSchema):
    spec: str = Field(min_length=1)
    score: float = Field(ge=0, le=1)
    operations: int = Field(ge=0)
    findings: list[str] = []


TOP_LEVEL = [OpenApiOperation, OpenApiDiffReport, OpenApiReadinessReport]

EXAMPLES = {
    "OpenApiOperation": {"operation_id": "listRuns", "method": "get", "path": "/runs",
                         "summary": "List generation runs", "tags": ["runs"],
                         "has_response_schema": True},
    "OpenApiDiffReport": {"old": "petstore-v1.yaml", "new": "petstore-v2.yaml",
                          "entries": [{"kind": "added", "pointer": "/paths/~1runs", "detail": "new path"}]},
    "OpenApiReadinessReport": {"spec": "petstore.yaml", "score": 0.85, "operations": 12,
                               "findings": ["2 operations missing summaries"]},
}
