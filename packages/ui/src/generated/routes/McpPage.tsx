// generated from design.yaml route `/mcp` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { McpToolBrowser } from "../components/McpToolBrowser";
import { NavSidebar } from "../components/NavSidebar";
import { mcp_tools } from "../fixtures/mcp_tools";

export function McpPage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <McpToolBrowser records={mcp_tools} />
          </>
        }
      />
    </SelectionProvider>
  );
}
