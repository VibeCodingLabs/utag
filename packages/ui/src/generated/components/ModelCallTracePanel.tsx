// generated from design.yaml component `model-call-trace-panel` — do not edit by hand
import React from "react";

export type ModelCallTracePanelState = "idle";

export interface ModelCallTracePanelProps {
  resource?: string;
  state?: ModelCallTracePanelState;
  children?: React.ReactNode;
}

export function ModelCallTracePanel({ state = "idle", children }: ModelCallTracePanelProps) {
  return (
    <section role="region" aria-label="model-call-trace-panel" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
