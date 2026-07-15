// generated from design.yaml component `run-timeline` — do not edit by hand
import React from "react";
import type { RunTrace } from "../schemas/contracts";

export type RunTimelineState = "idle" | "loading";

export interface RunTimelineProps {
  records?: RunTrace[];
  state?: RunTimelineState;
  children?: React.ReactNode;
}

export function RunTimeline({ records = [], state = "idle", children }: RunTimelineProps) {
  const max = Math.max(1, ...records.flatMap((r) => (r.spans ?? []).map((s) => s.end_ms)));
  return (
    <section role="region" aria-label="run-timeline" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>
      {records.map((r, i) => (
        <div key={i} aria-label={r.run_id}>
          <h4>{r.run_id}</h4>
          {(r.spans ?? []).map((s, j) => (
            <div key={j} title={`${s.name} (${s.start_ms}–${s.end_ms}ms)`}
              style={{
                marginLeft: `${(s.start_ms / max) * 100}%`,
                width: `${Math.max(1, ((s.end_ms - s.start_ms) / max) * 100)}%`,
                background: "var(--utag-color-accent)",
                color: "var(--utag-color-bg)",
                borderRadius: "var(--utag-radius-sm)",
                marginBottom: "var(--utag-space-1)",
                paddingLeft: "var(--utag-space-1)",
              }}>
              {s.name}
            </div>
          ))}
        </div>
      ))}
      {children}
    </section>
  );
}
