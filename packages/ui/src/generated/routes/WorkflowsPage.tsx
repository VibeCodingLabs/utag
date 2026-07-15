// generated from design.yaml route `/workflows` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { ArazzoWorkflowGraph } from "../components/ArazzoWorkflowGraph";
import { NavSidebar } from "../components/NavSidebar";
import { workflows } from "../fixtures/workflows";

export function WorkflowsPage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <ArazzoWorkflowGraph records={workflows} />
          </>
        }
      />
    </SelectionProvider>
  );
}
