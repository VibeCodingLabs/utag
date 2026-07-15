// generated from design.yaml component `generator-coverage-matrix` — do not edit by hand
import React from "react";

export type GeneratorCoverageMatrixState = "idle";

export interface GeneratorCoverageMatrixProps {
  resource?: string;
  state?: GeneratorCoverageMatrixState;
  children?: React.ReactNode;
}

export function GeneratorCoverageMatrix({ state = "idle", children }: GeneratorCoverageMatrixProps) {
  return (
    <table aria-label="generator-coverage-matrix" data-state={state}>
      <tbody>{children}</tbody>
    </table>
  );
}
