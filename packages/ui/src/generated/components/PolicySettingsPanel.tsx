// generated from design.yaml component `policy-settings-panel` — do not edit by hand
import React from "react";
import type { ModelRouterPolicy } from "../schemas/contracts";

export type PolicySettingsPanelState = "idle";

export interface PolicySettingsPanelProps {
  records?: ModelRouterPolicy[];
  state?: PolicySettingsPanelState;
  children?: React.ReactNode;
}

export function PolicySettingsPanel({ records = [], state = "idle", children }: PolicySettingsPanelProps) {
  
  const record = records[0];
  return (
    <section role="region" aria-label="policy-settings-panel" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>
      {record ? (
        <dl>
          <dt>task_kind</dt><dd>{String(record.task_kind ?? "")}</dd>
          <dt>max_cost_usd</dt><dd>{String(record.max_cost_usd ?? "")}</dd>
          <dt>max_latency_ms</dt><dd>{String(record.max_latency_ms ?? "")}</dd>
          <dt>require_structured_output</dt><dd>{String(record.require_structured_output ?? "")}</dd>
          <dt>local_only</dt><dd>{String(record.local_only ?? "")}</dd>
          <dt>no_network</dt><dd>{String(record.no_network ?? "")}</dd>
          <dt>allow_fallback</dt><dd>{String(record.allow_fallback ?? "")}</dd>
          <dt>prefer_cached</dt><dd>{String(record.prefer_cached ?? "")}</dd>
        </dl>
      ) : (
        <p>No data</p>
      )}
      {children}
    </section>
  );
}
