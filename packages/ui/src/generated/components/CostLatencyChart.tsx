// generated from design.yaml component `cost-latency-chart` — do not edit by hand
import React from "react";

export type CostLatencyChartState = "idle";

export interface CostLatencyChartProps {
  resource?: string;
  state?: CostLatencyChartState;
  children?: React.ReactNode;
}

export function CostLatencyChart({ state = "idle", children }: CostLatencyChartProps) {
  return (
    <section role="region" aria-label="cost-latency-chart" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
