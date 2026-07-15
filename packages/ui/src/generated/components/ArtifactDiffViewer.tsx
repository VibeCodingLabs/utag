// generated from design.yaml component `artifact-diff-viewer` — do not edit by hand
import React from "react";

export type ArtifactDiffViewerState = "idle";

export interface ArtifactDiffViewerProps {
  resource?: string;
  state?: ArtifactDiffViewerState;
  children?: React.ReactNode;
}

export function ArtifactDiffViewer({ state = "idle", children }: ArtifactDiffViewerProps) {
  return (
    <section role="region" aria-label="artifact-diff-viewer" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
