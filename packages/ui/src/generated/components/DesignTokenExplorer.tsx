// generated from design.yaml component `design-token-explorer` — do not edit by hand
import React from "react";

export type DesignTokenExplorerState = "idle";

export interface DesignTokenExplorerProps {
  resource?: string;
  state?: DesignTokenExplorerState;
  children?: React.ReactNode;
}

export function DesignTokenExplorer({ state = "idle", children }: DesignTokenExplorerProps) {
  return (
    <table aria-label="design-token-explorer" data-state={state}>
      <tbody>{children}</tbody>
    </table>
  );
}
