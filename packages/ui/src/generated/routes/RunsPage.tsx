// generated from design.yaml route `/runs` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { RunTable } from "../components/RunTable";
import { RunInspector } from "../components/RunInspector";
import { RunTimeline } from "../components/RunTimeline";
import { NavSidebar } from "../components/NavSidebar";
import { runs } from "../fixtures/runs";

export function RunsPage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <RunTable records={runs} />
            <RunTimeline records={runs} />
          </>
        }
        inspector={
          <>
            <RunInspector records={runs} />
          </>
        }
      />
    </SelectionProvider>
  );
}
