// generated from design.yaml component `artifact-manifest-panel` — do not edit by hand
import React from "react";
import type { ArtifactManifest } from "../schemas/contracts";
import { useSelect } from "../hooks/useInteractions";

export type ArtifactManifestPanelState = "idle";

export interface ArtifactManifestPanelProps {
  records?: ArtifactManifest[];
  state?: ArtifactManifestPanelState;
  children?: React.ReactNode;
}

export function ArtifactManifestPanel({ records = [], state = "idle", children }: ArtifactManifestPanelProps) {
  const select = useSelect();
  const record = records[0];
  return (
    <section role="region" aria-label="artifact-manifest-panel" data-state={state} tabIndex={0}
      onClick={() => { if (record) { select("select-artifact", record); } }}
      onKeyDown={(e: { key: string }) => { if (e.key === "Enter" && record) { select("select-artifact", record); } }}
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
