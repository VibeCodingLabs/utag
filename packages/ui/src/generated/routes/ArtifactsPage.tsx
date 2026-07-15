// generated from design.yaml route `/artifacts` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { ArtifactDiffViewer } from "../components/ArtifactDiffViewer";
import { ArtifactManifestPanel } from "../components/ArtifactManifestPanel";

export function ArtifactsPage() {
  return (
    <ConsoleShell
      main={
        <>
        <ArtifactManifestPanel />
        <ArtifactDiffViewer />
        </>
      }
    />
  );
}
