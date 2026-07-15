// generated from design.yaml route `/workflows` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { ArazzoWorkflowGraph } from "../components/ArazzoWorkflowGraph";

export function WorkflowsPage() {
  return (
    <ConsoleShell
      main={
        <>
        <ArazzoWorkflowGraph />
        </>
      }
    />
  );
}
