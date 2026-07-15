// generated from design.yaml component `run-status-card` — do not edit by hand
import React from "react";

export type RunStatusCardState = "idle" | "loading" | "error";

export interface RunStatusCardProps {
  title?: string;
  state?: RunStatusCardState;
  children?: React.ReactNode;
}

export function RunStatusCard({ state = "idle", children }: RunStatusCardProps) {
  return (
    <section role="group" aria-label="run-status-card" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
