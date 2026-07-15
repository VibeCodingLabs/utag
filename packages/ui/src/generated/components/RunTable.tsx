// generated from design.yaml component `run-table` — do not edit by hand
import React from "react";
import type { RunTrace } from "../schemas/contracts";
import { useSelect } from "../hooks/useInteractions";

export type RunTableState = "idle";

export interface RunTableProps {
  records?: RunTrace[];
  state?: RunTableState;
  children?: React.ReactNode;
}

export function RunTable({ records = [], state = "idle", children }: RunTableProps) {
  const select = useSelect();
  return (
    <table aria-label="run-table" data-state={state}>
      <thead>
        <tr><th>run_id</th></tr>
      </thead>
      <tbody>
        {records.map((r, i) => (
          <tr key={i} tabIndex={0}
              onClick={() => { select("select-run", r); }}
              onKeyDown={(e: { key: string }) => { if (e.key === "Enter") { select("select-run", r); } }}>
            <td>{String(r.run_id ?? "")}</td>
          </tr>
        ))}
      </tbody>
      {children}
    </table>
  );
}
