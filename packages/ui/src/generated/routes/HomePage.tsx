// generated from design.yaml route `/` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { CostLatencyChart } from "../components/CostLatencyChart";
import { RunStatusCard } from "../components/RunStatusCard";
import { RunTimeline } from "../components/RunTimeline";

export function HomePage() {
  return (
    <ConsoleShell
      main={
        <>
        <RunStatusCard />
        <RunTimeline />
        <CostLatencyChart />
        </>
      }
    />
  );
}
