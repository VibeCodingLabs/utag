// generated from design.yaml route `/runs` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { RunInspector } from "../components/RunInspector";
import { RunTable } from "../components/RunTable";

export function RunsPage() {
  return (
    <ConsoleShell
      main={
        <>
        <RunTable />
        <RunInspector />
        </>
      }
    />
  );
}
