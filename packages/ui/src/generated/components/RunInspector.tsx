// generated from design.yaml component `run-inspector` — do not edit by hand
import React from "react";

export type RunInspectorState = "idle";

export interface RunInspectorProps {
  resource?: string;
  state?: RunInspectorState;
  children?: React.ReactNode;
}

export function RunInspector({ state = "idle", children }: RunInspectorProps) {
  return (
    <section role="region" aria-label="run-inspector" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
