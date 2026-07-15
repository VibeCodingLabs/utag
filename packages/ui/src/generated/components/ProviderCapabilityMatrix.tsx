// generated from design.yaml component `provider-capability-matrix` — do not edit by hand
import React from "react";
import type { AIProviderManifest } from "../schemas/contracts";

export type ProviderCapabilityMatrixState = "idle";

export interface ProviderCapabilityMatrixProps {
  records?: AIProviderManifest[];
  state?: ProviderCapabilityMatrixState;
  children?: React.ReactNode;
}

export function ProviderCapabilityMatrix({ records = [], state = "idle", children }: ProviderCapabilityMatrixProps) {
  
  return (
    <table aria-label="provider-capability-matrix" data-state={state} style={{ font: "var(--utag-font-mono)" }}>
      <thead>
        <tr><th>id</th><th>name</th></tr>
      </thead>
      <tbody>
        {records.map((r, i) => (
          <tr key={i} tabIndex={0}>
            <td>{String(r.id ?? "")}</td><td>{String(r.name ?? "")}</td>
          </tr>
        ))}
      </tbody>
      {children}
    </table>
  );
}
