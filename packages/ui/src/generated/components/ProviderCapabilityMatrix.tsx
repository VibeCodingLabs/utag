// generated from design.yaml component `provider-capability-matrix` — do not edit by hand
import React from "react";

export type ProviderCapabilityMatrixState = "idle";

export interface ProviderCapabilityMatrixProps {
  resource?: string;
  state?: ProviderCapabilityMatrixState;
  children?: React.ReactNode;
}

export function ProviderCapabilityMatrix({ state = "idle", children }: ProviderCapabilityMatrixProps) {
  return (
    <table aria-label="provider-capability-matrix" data-state={state}>
      <tbody>{children}</tbody>
    </table>
  );
}
