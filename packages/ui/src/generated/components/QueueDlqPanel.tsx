// generated from design.yaml component `queue-dlq-panel` — do not edit by hand
import React from "react";

export type QueueDlqPanelState = "idle";

export interface QueueDlqPanelProps {
  resource?: string;
  state?: QueueDlqPanelState;
  children?: React.ReactNode;
}

export function QueueDlqPanel({ state = "idle", children }: QueueDlqPanelProps) {
  return (
    <section role="region" aria-label="queue-dlq-panel" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
