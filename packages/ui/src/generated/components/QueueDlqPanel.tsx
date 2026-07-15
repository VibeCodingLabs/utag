// generated from design.yaml component `queue-dlq-panel` — do not edit by hand
import React from "react";
import type { WorkerJobTrace } from "../schemas/contracts";

export type QueueDlqPanelState = "idle";

export interface QueueDlqPanelProps {
  records?: WorkerJobTrace[];
  state?: QueueDlqPanelState;
  children?: React.ReactNode;
}

export function QueueDlqPanel({ records = [], state = "idle", children }: QueueDlqPanelProps) {
  return (
    <section role="region" aria-label="queue-dlq-panel" data-state={state} tabIndex={0}
      style={{ display: "grid", gridAutoFlow: "column", gap: "var(--utag-space-2)" }}>
        <section key="queued" aria-label="queued">
          <h4>queued</h4>
          {records.filter((r) => r.status === "queued").map((r, i) => (
            <div key={i} tabIndex={0} style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>{String(r.job_id)}</div>
          ))}
        </section>
        <section key="running" aria-label="running">
          <h4>running</h4>
          {records.filter((r) => r.status === "running").map((r, i) => (
            <div key={i} tabIndex={0} style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>{String(r.job_id)}</div>
          ))}
        </section>
        <section key="completed" aria-label="completed">
          <h4>completed</h4>
          {records.filter((r) => r.status === "completed").map((r, i) => (
            <div key={i} tabIndex={0} style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>{String(r.job_id)}</div>
          ))}
        </section>
        <section key="failed" aria-label="failed">
          <h4>failed</h4>
          {records.filter((r) => r.status === "failed").map((r, i) => (
            <div key={i} tabIndex={0} style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>{String(r.job_id)}</div>
          ))}
        </section>
        <section key="dead-letter" aria-label="dead-letter">
          <h4>dead-letter</h4>
          {records.filter((r) => r.status === "dead-letter").map((r, i) => (
            <div key={i} tabIndex={0} style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>{String(r.job_id)}</div>
          ))}
        </section>
      {children}
    </section>
  );
}
