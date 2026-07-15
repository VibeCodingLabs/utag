// generated from design.yaml component `schema-validation-inspector` — do not edit by hand
import React from "react";
import type { ValidationReport } from "../schemas/contracts";
import { useSelected } from "../hooks/useInteractions";

export type SchemaValidationInspectorState = "idle";

export interface SchemaValidationInspectorProps {
  records?: ValidationReport[];
  state?: SchemaValidationInspectorState;
  children?: React.ReactNode;
}

export function SchemaValidationInspector({ records = [], state = "idle", children }: SchemaValidationInspectorProps) {
  
  const selected = useSelected("select-validation-finding") as ValidationReport | undefined;
  const record = selected ?? records[0];
  return (
    <section role="region" aria-label="schema-validation-inspector" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>
      {record ? (
        <dl>
          <dt>artifact_id</dt><dd>{String(record.artifact_id ?? "")}</dd>
          <dt>valid</dt><dd>{String(record.valid ?? "")}</dd>
          <dt>findings</dt><dd><pre>{JSON.stringify(record.findings, null, 2)}</pre></dd>
          <dt>run_id</dt><dd>{String(record.run_id ?? "")}</dd>
          <dt>span_id</dt><dd>{String(record.span_id ?? "")}</dd>
        </dl>
      ) : (
        <p>No data</p>
      )}
      {children}
    </section>
  );
}
