// generated from design.yaml route `/registry` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { GeneratorCoverageMatrix } from "../components/GeneratorCoverageMatrix";
import { NavSidebar } from "../components/NavSidebar";
import { registry } from "../fixtures/registry";

export function RegistryPage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <GeneratorCoverageMatrix records={registry} />
          </>
        }
      />
    </SelectionProvider>
  );
}
