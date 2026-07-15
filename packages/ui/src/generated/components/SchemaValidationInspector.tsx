// generated from design.yaml component `schema-validation-inspector` — do not edit by hand
import React from "react";

export type SchemaValidationInspectorState = "idle";

export interface SchemaValidationInspectorProps {
  resource?: string;
  state?: SchemaValidationInspectorState;
  children?: React.ReactNode;
}

export function SchemaValidationInspector({ state = "idle", children }: SchemaValidationInspectorProps) {
  return (
    <section role="region" aria-label="schema-validation-inspector" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
