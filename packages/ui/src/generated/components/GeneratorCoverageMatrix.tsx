// generated from design.yaml component `generator-coverage-matrix` — do not edit by hand
import React from "react";
import type { GeneratorManifest } from "../schemas/contracts";

export type GeneratorCoverageMatrixState = "idle";

export interface GeneratorCoverageMatrixProps {
  records?: GeneratorManifest[];
  state?: GeneratorCoverageMatrixState;
  children?: React.ReactNode;
}

export function GeneratorCoverageMatrix({ records = [], state = "idle", children }: GeneratorCoverageMatrixProps) {
  
  return (
    <table aria-label="generator-coverage-matrix" data-state={state} style={{ font: "var(--utag-font-mono)" }}>
      <thead>
        <tr><th>id</th><th>name</th><th>version</th><th>input_schema</th><th>output_schema</th><th>risk_level</th></tr>
      </thead>
      <tbody>
        {records.map((r, i) => (
          <tr key={i} tabIndex={0}>
            <td>{String(r.id ?? "")}</td><td>{String(r.name ?? "")}</td><td>{String(r.version ?? "")}</td><td>{String(r.input_schema ?? "")}</td><td>{String(r.output_schema ?? "")}</td><td>{String(r.risk_level ?? "")}</td>
          </tr>
        ))}
      </tbody>
      {children}
    </table>
  );
}
