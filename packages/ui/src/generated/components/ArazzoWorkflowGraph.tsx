// generated from design.yaml component `arazzo-workflow-graph` — do not edit by hand
import React from "react";

export type ArazzoWorkflowGraphState = "idle";

export interface ArazzoWorkflowGraphProps {
  resource?: string;
  state?: ArazzoWorkflowGraphState;
  children?: React.ReactNode;
}

export function ArazzoWorkflowGraph({ state = "idle", children }: ArazzoWorkflowGraphProps) {
  return (
    <section role="region" aria-label="arazzo-workflow-graph" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
