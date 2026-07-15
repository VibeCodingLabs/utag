// generated from design.yaml route `/tokens` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { DesignTokenExplorer } from "../components/DesignTokenExplorer";
import { NavSidebar } from "../components/NavSidebar";
import { design_tokens } from "../fixtures/design_tokens";

export function TokensPage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <DesignTokenExplorer records={design_tokens} />
          </>
        }
      />
    </SelectionProvider>
  );
}
