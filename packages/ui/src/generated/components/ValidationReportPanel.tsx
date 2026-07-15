// generated from design.yaml component `validation-report-panel` — do not edit by hand
import React from "react";
import type { ValidationReport } from "../schemas/contracts";
import { useSelect } from "../hooks/useInteractions";

export type ValidationReportPanelState = "idle";

export interface ValidationReportPanelProps {
  records?: ValidationReport[];
  state?: ValidationReportPanelState;
  children?: React.ReactNode;
}

export function ValidationReportPanel({ records = [], state = "idle", children }: ValidationReportPanelProps) {
  const select = useSelect();
  const record = records[0];
  return (
    <section role="region" aria-label="validation-report-panel" data-state={state} tabIndex={0}
      onClick={() => { if (record) { select("select-validation-finding", record); } }}
      onKeyDown={(e: { key: string }) => { if (e.key === "Enter" && record) { select("select-validation-finding", record); } }}
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
