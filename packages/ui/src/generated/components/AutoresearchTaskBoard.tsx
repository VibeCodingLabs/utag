// generated from design.yaml component `autoresearch-task-board` — do not edit by hand
import React from "react";

export type AutoresearchTaskBoardState = "idle";

export interface AutoresearchTaskBoardProps {
  resource?: string;
  state?: AutoresearchTaskBoardState;
  children?: React.ReactNode;
}

export function AutoresearchTaskBoard({ state = "idle", children }: AutoresearchTaskBoardProps) {
  return (
    <section role="region" aria-label="autoresearch-task-board" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
