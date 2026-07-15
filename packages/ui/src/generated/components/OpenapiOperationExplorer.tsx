// generated from design.yaml component `openapi-operation-explorer` — do not edit by hand
import React from "react";
import type { OpenApiOperation } from "../schemas/contracts";

export type OpenapiOperationExplorerState = "idle";

export interface OpenapiOperationExplorerProps {
  records?: OpenApiOperation[];
  state?: OpenapiOperationExplorerState;
  children?: React.ReactNode;
}

export function OpenapiOperationExplorer({ records = [], state = "idle", children }: OpenapiOperationExplorerProps) {
  
  return (
    <table aria-label="openapi-operation-explorer" data-state={state}>
      <thead>
        <tr><th>operation_id</th><th>method</th><th>path</th><th>summary</th><th>has_request_schema</th><th>has_response_schema</th></tr>
      </thead>
      <tbody>
        {records.map((r, i) => (
          <tr key={i} tabIndex={0}>
            <td>{String(r.operation_id ?? "")}</td><td>{String(r.method ?? "")}</td><td>{String(r.path ?? "")}</td><td>{String(r.summary ?? "")}</td><td>{String(r.has_request_schema ?? "")}</td><td>{String(r.has_response_schema ?? "")}</td>
          </tr>
        ))}
      </tbody>
      {children}
    </table>
  );
}
