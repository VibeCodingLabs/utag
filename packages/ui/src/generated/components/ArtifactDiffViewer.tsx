// generated from design.yaml component `artifact-diff-viewer` — do not edit by hand
import React from "react";
import type { ArtifactManifest } from "../schemas/contracts";
import { useSelected } from "../hooks/useInteractions";

export type ArtifactDiffViewerState = "idle";

export interface ArtifactDiffViewerProps {
  records?: ArtifactManifest[];
  state?: ArtifactDiffViewerState;
  children?: React.ReactNode;
}

export function ArtifactDiffViewer({ records = [], state = "idle", children }: ArtifactDiffViewerProps) {
  
  const selected = useSelected("select-artifact") as ArtifactManifest | undefined;
  const record = selected ?? records[0];
  return (
    <section role="region" aria-label="artifact-diff-viewer" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)", padding: "var(--utag-space-2)", borderRadius: "var(--utag-radius-md)" }}>
      {record ? (
        <dl>
          <dt>id</dt><dd>{String(record.id ?? "")}</dd>
          <dt>target</dt><dd>{String(record.target ?? "")}</dd>
          <dt>files</dt><dd><pre>{JSON.stringify(record.files, null, 2)}</pre></dd>
          <dt>provenance</dt><dd><pre>{JSON.stringify(record.provenance, null, 2)}</pre></dd>
          <dt>deterministic</dt><dd>{String(record.deterministic ?? "")}</dd>
        </dl>
      ) : (
        <p>No data</p>
      )}
      {children}
    </section>
  );
}
