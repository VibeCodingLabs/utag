// generated from design.yaml component `run-timeline` — do not edit by hand
import React from "react";

export type RunTimelineState = "idle" | "loading";

export interface RunTimelineProps {
  resource?: string;
  state?: RunTimelineState;
  children?: React.ReactNode;
}

export function RunTimeline({ state = "idle", children }: RunTimelineProps) {
  return (
    <section role="region" aria-label="run-timeline" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
