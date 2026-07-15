// generated from design.yaml component `run-table` — do not edit by hand
import React from "react";

export type RunTableState = "idle";

export interface RunTableProps {
  resource?: string;
  state?: RunTableState;
  children?: React.ReactNode;
}

export function RunTable({ state = "idle", children }: RunTableProps) {
  return (
    <table aria-label="run-table" data-state={state}>
      <tbody>{children}</tbody>
    </table>
  );
}
