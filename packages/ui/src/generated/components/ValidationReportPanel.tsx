// generated from design.yaml component `validation-report-panel` — do not edit by hand
import React from "react";

export type ValidationReportPanelState = "idle";

export interface ValidationReportPanelProps {
  resource?: string;
  state?: ValidationReportPanelState;
  children?: React.ReactNode;
}

export function ValidationReportPanel({ state = "idle", children }: ValidationReportPanelProps) {
  return (
    <section role="region" aria-label="validation-report-panel" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
