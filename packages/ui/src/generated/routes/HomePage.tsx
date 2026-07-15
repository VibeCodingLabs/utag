// generated from design.yaml route `/` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { RunStatusCard } from "../components/RunStatusCard";
import { RunTimeline } from "../components/RunTimeline";
import { CostLatencyChart } from "../components/CostLatencyChart";
import { NavSidebar } from "../components/NavSidebar";
import { metrics } from "../fixtures/metrics";
import { runs } from "../fixtures/runs";

export function HomePage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <RunStatusCard records={runs} />
            <RunTimeline records={runs} />
            <CostLatencyChart records={metrics} />
          </>
        }
      />
    </SelectionProvider>
  );
}
