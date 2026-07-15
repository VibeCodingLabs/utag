// generated from design.yaml component `openapi-operation-explorer` — do not edit by hand
import React from "react";

export type OpenapiOperationExplorerState = "idle";

export interface OpenapiOperationExplorerProps {
  resource?: string;
  state?: OpenapiOperationExplorerState;
  children?: React.ReactNode;
}

export function OpenapiOperationExplorer({ state = "idle", children }: OpenapiOperationExplorerProps) {
  return (
    <table aria-label="openapi-operation-explorer" data-state={state}>
      <tbody>{children}</tbody>
    </table>
  );
}
