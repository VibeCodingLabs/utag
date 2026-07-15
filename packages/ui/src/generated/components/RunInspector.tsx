// generated from design.yaml component `run-inspector` — do not edit by hand
import React from "react";
import type { RunTrace } from "../schemas/contracts";
import { useSelected } from "../hooks/useInteractions";

export type RunInspectorState = "idle";

export interface RunInspectorProps {
  records?: RunTrace[];
  state?: RunInspectorState;
  children?: React.ReactNode;
}

export function RunInspector({ records = [], state = "idle", children }: RunInspectorProps) {
  
  const selected = useSelected("select-run") as RunTrace | undefined;
  const record = selected ?? records[0];
  return (
    <section role="region" aria-label="run-inspector" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>
      {record ? (
        <dl>
          <dt>run_id</dt><dd>{String(record.run_id ?? "")}</dd>
          <dt>spans</dt><dd><pre>{JSON.stringify(record.spans, null, 2)}</pre></dd>
        </dl>
      ) : (
        <p>No data</p>
      )}
      {children}
    </section>
  );
}
