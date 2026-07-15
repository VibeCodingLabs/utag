// generated from design.yaml component `model-call-trace-panel` — do not edit by hand
import React from "react";
import type { ModelCallTrace } from "../schemas/contracts";

export type ModelCallTracePanelState = "idle";

export interface ModelCallTracePanelProps {
  records?: ModelCallTrace[];
  state?: ModelCallTracePanelState;
  children?: React.ReactNode;
}

export function ModelCallTracePanel({ records = [], state = "idle", children }: ModelCallTracePanelProps) {
  
  const record = records[0];
  return (
    <section role="region" aria-label="model-call-trace-panel" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>
      {record ? (
        <dl>
          <dt>run_id</dt><dd>{String(record.run_id ?? "")}</dd>
          <dt>provider</dt><dd>{String(record.provider ?? "")}</dd>
          <dt>model</dt><dd>{String(record.model ?? "")}</dd>
          <dt>prompt_sha256</dt><dd>{String(record.prompt_sha256 ?? "")}</dd>
          <dt>output_sha256</dt><dd>{String(record.output_sha256 ?? "")}</dd>
          <dt>input_tokens</dt><dd>{String(record.input_tokens ?? "")}</dd>
          <dt>output_tokens</dt><dd>{String(record.output_tokens ?? "")}</dd>
          <dt>cost_usd</dt><dd>{String(record.cost_usd ?? "")}</dd>
          <dt>latency_ms</dt><dd>{String(record.latency_ms ?? "")}</dd>
        </dl>
      ) : (
        <p>No data</p>
      )}
      {children}
    </section>
  );
}
