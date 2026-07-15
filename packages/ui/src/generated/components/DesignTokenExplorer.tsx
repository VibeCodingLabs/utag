// generated from design.yaml component `design-token-explorer` — do not edit by hand
import React from "react";
import type { CssVariableManifest } from "../schemas/contracts";

export type DesignTokenExplorerState = "idle";

export interface DesignTokenExplorerProps {
  records?: CssVariableManifest[];
  state?: DesignTokenExplorerState;
  children?: React.ReactNode;
}

export function DesignTokenExplorer({ records = [], state = "idle", children }: DesignTokenExplorerProps) {
  
  const record = records[0];
  return (
    <section role="region" aria-label="design-token-explorer" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>
      {record ? (
        <dl>
          <dt>file</dt><dd>{String(record.file ?? "")}</dd>
          <dt>variables</dt><dd><pre>{JSON.stringify(record.variables, null, 2)}</pre></dd>
          <dt>source_design</dt><dd>{String(record.source_design ?? "")}</dd>
        </dl>
      ) : (
        <p>No data</p>
      )}
      {children}
    </section>
  );
}
