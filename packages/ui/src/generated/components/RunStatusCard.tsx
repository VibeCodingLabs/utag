// generated from design.yaml component `run-status-card` — do not edit by hand
import React from "react";
import type { RunTrace } from "../schemas/contracts";

export type RunStatusCardState = "idle" | "loading" | "error";

export interface RunStatusCardProps {
  records?: RunTrace[];
  state?: RunStatusCardState;
  children?: React.ReactNode;
}

export function RunStatusCard({ records = [], state = "idle", children }: RunStatusCardProps) {
  return (
    <section role="group" aria-label="run-status-card" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>
      <h3>Run status</h3>
      <p>{records.length} record(s)</p>
      <p>latest: {records.length ? String(records[0].run_id) : "—"}</p>
      {children}
    </section>
  );
}
