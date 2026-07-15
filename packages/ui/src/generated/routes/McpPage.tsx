// generated from design.yaml route `/mcp` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { McpToolBrowser } from "../components/McpToolBrowser";

export function McpPage() {
  return (
    <ConsoleShell
      main={
        <>
        <McpToolBrowser />
        </>
      }
    />
  );
}
