// generated from design.yaml route `/openapi` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { OpenapiOperationExplorer } from "../components/OpenapiOperationExplorer";
import { NavSidebar } from "../components/NavSidebar";
import { openapi_operations } from "../fixtures/openapi_operations";

export function OpenapiPage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <OpenapiOperationExplorer records={openapi_operations} />
          </>
        }
      />
    </SelectionProvider>
  );
}
