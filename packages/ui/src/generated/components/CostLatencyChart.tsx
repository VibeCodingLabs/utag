// generated from design.yaml component `cost-latency-chart` — do not edit by hand
import React from "react";
import type { MetricPoint } from "../schemas/contracts";

export type CostLatencyChartState = "idle";

export interface CostLatencyChartProps {
  records?: MetricPoint[];
  state?: CostLatencyChartState;
  children?: React.ReactNode;
}

export function CostLatencyChart({ records = [], state = "idle", children }: CostLatencyChartProps) {
  const max = Math.max(1, ...records.map((r) => r.value));
  return (
    <section role="region" aria-label="cost-latency-chart" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>
      {records.map((r, i) => (
        <div key={i}>
          <span>{r.name}: {r.value}</span>
          <div role="img" aria-label={`${r.name} ${r.value}`}
            style={{
              width: `${(r.value / max) * 100}%`,
              background: "var(--utag-color-accent)",
              height: "var(--utag-space-2)",
              borderRadius: "var(--utag-radius-sm)",
            }} />
        </div>
      ))}
      {children}
    </section>
  );
}
