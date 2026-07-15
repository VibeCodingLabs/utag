// generated from design.yaml component `mcp-tool-browser` — do not edit by hand
import React from "react";
import type { MCPToolContract } from "../schemas/contracts";

export type McpToolBrowserState = "idle";

export interface McpToolBrowserProps {
  records?: MCPToolContract[];
  state?: McpToolBrowserState;
  children?: React.ReactNode;
}

export function McpToolBrowser({ records = [], state = "idle", children }: McpToolBrowserProps) {
  
  return (
    <table aria-label="mcp-tool-browser" data-state={state}>
      <thead>
        <tr><th>name</th><th>description</th><th>side_effect</th><th>policy_status</th></tr>
      </thead>
      <tbody>
        {records.map((r, i) => (
          <tr key={i} tabIndex={0}>
            <td>{String(r.name ?? "")}</td><td>{String(r.description ?? "")}</td><td>{String(r.side_effect ?? "")}</td><td>{String(r.policy_status ?? "")}</td>
          </tr>
        ))}
      </tbody>
      {children}
    </table>
  );
}
