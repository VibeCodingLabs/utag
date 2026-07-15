// generated from design.yaml component `artifact-manifest-panel` — do not edit by hand
import React from "react";

export type ArtifactManifestPanelState = "idle";

export interface ArtifactManifestPanelProps {
  resource?: string;
  state?: ArtifactManifestPanelState;
  children?: React.ReactNode;
}

export function ArtifactManifestPanel({ state = "idle", children }: ArtifactManifestPanelProps) {
  return (
    <section role="region" aria-label="artifact-manifest-panel" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
