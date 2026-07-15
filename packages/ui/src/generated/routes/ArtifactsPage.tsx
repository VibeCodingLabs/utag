// generated from design.yaml route `/artifacts` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { ArtifactManifestPanel } from "../components/ArtifactManifestPanel";
import { ArtifactDiffViewer } from "../components/ArtifactDiffViewer";
import { NavSidebar } from "../components/NavSidebar";
import { artifacts } from "../fixtures/artifacts";

export function ArtifactsPage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <ArtifactManifestPanel records={artifacts} />
          </>
        }
        inspector={
          <>
            <ArtifactDiffViewer records={artifacts} />
          </>
        }
      />
    </SelectionProvider>
  );
}
