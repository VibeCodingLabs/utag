// generated from design.yaml route `/openapi` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { OpenapiOperationExplorer } from "../components/OpenapiOperationExplorer";

export function OpenapiPage() {
  return (
    <ConsoleShell
      main={
        <>
        <OpenapiOperationExplorer />
        </>
      }
    />
  );
}
