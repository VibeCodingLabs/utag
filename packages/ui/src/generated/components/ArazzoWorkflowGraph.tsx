// generated from design.yaml component `arazzo-workflow-graph` — do not edit by hand
import React from "react";
import type { AutoresearchPlan } from "../schemas/contracts";

export type ArazzoWorkflowGraphState = "idle";

export interface ArazzoWorkflowGraphProps {
  records?: AutoresearchPlan[];
  state?: ArazzoWorkflowGraphState;
  children?: React.ReactNode;
}

export function ArazzoWorkflowGraph({ records = [], state = "idle", children }: ArazzoWorkflowGraphProps) {
  return (
    <nav aria-label="arazzo-workflow-graph" data-state={state}>
      <ol style={{ display: "flex", listStyle: "none", gap: "var(--utag-space-2)" }}>
        {records.map((r, i) => (
          <li key={i} tabIndex={0} style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>
            {i > 0 ? <span aria-hidden="true">→ </span> : null}
            {String(r.task_id)}
          </li>
        ))}
      </ol>
      {children}
    </nav>
  );
}
