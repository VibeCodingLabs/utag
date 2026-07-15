// generated from design.yaml component `mcp-tool-browser` — do not edit by hand
import React from "react";

export type McpToolBrowserState = "idle";

export interface McpToolBrowserProps {
  resource?: string;
  state?: McpToolBrowserState;
  children?: React.ReactNode;
}

export function McpToolBrowser({ state = "idle", children }: McpToolBrowserProps) {
  return (
    <table aria-label="mcp-tool-browser" data-state={state}>
      <tbody>{children}</tbody>
    </table>
  );
}
