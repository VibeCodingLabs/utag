// generated from design.yaml component `autoresearch-task-board` — do not edit by hand
import React from "react";
import type { AutoresearchTask } from "../schemas/contracts";

export type AutoresearchTaskBoardState = "idle";

export interface AutoresearchTaskBoardProps {
  records?: AutoresearchTask[];
  state?: AutoresearchTaskBoardState;
  children?: React.ReactNode;
}

export function AutoresearchTaskBoard({ records = [], state = "idle", children }: AutoresearchTaskBoardProps) {
  return (
    <section role="region" aria-label="autoresearch-task-board" data-state={state} tabIndex={0}
      style={{ display: "grid", gridAutoFlow: "column", gap: "var(--utag-space-2)" }}>
        <section key="research" aria-label="research">
          <h4>research</h4>
          {records.filter((r) => r.mode === "research").map((r, i) => (
            <div key={i} tabIndex={0} style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>{String(r.id)}</div>
          ))}
        </section>
        <section key="implement" aria-label="implement">
          <h4>implement</h4>
          {records.filter((r) => r.mode === "implement").map((r, i) => (
            <div key={i} tabIndex={0} style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>{String(r.id)}</div>
          ))}
        </section>
        <section key="dry-run" aria-label="dry-run">
          <h4>dry-run</h4>
          {records.filter((r) => r.mode === "dry-run").map((r, i) => (
            <div key={i} tabIndex={0} style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>{String(r.id)}</div>
          ))}
        </section>
      {children}
    </section>
  );
}
