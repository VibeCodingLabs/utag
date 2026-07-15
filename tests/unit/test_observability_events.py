"""Recorder: span nesting, events, metrics; JSONL validates against schemas."""
from __future__ import annotations

from utag_core.observe import Recorder, validate_jsonl
from utag_core.schemas.observability import RunTrace


def test_span_nesting_and_trace():
    rec = Recorder(run_id="run-test")
    with rec.span("utag.run", target="zod-schemas"):
        with rec.span("utag.generate"):
            pass
        with rec.span("utag.validate"):
            rec.metric("utag_validation_failures_total", 0)
    trace = rec.trace()
    assert isinstance(trace, RunTrace) and trace.run_id == "run-test"
    by_name = {s.name: s for s in trace.spans}
    assert by_name["utag.generate"].parent_span_id == by_name["utag.run"].span_id
    assert by_name["utag.validate"].parent_span_id == by_name["utag.run"].span_id
    assert by_name["utag.run"].parent_span_id is None
    assert by_name["utag.run"].end_ms >= by_name["utag.generate"].end_ms
    assert by_name["utag.run"].attributes == {"target": "zod-schemas"}


def test_jsonl_roundtrip_validates():
    rec = Recorder(run_id="run-test")
    with rec.span("utag.run"):
        rec.event("utag.acquire", source="fixtures/x.yaml")
        rec.metric("utag_runs_total", 1, target="zod-schemas")
    assert validate_jsonl(rec.to_jsonl()) == []


def test_validate_jsonl_rejects_bad_records():
    assert validate_jsonl('{"kind": "metric-point", "record": {"name": "not_utag_prefixed", "value": 1}}\n')
    assert validate_jsonl('{"kind": "artifact-manifest", "record": {}}\n')  # not an observability kind
    assert validate_jsonl("not json\n")


def test_flush_writes_store(tmp_path):
    rec = Recorder(run_id="run-flush")
    with rec.span("utag.run"):
        pass
    path = rec.flush(tmp_path)
    assert path == tmp_path / "run-flush.jsonl"
    assert validate_jsonl(path.read_text()) == []
