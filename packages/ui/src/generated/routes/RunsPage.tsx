// generated from design.yaml route `/runs` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { RunInspector } from "../components/RunInspector";
import { RunTable } from "../components/RunTable";
import { RunTimeline } from "../components/RunTimeline";

export function RunsPage() {
  return (
    <ConsoleShell
      main={
        <>
        <RunTable />
        <RunInspector />
        <RunTimeline />
        </>
      }
    />
  );
}
