// generated from design.yaml route `/autoresearch` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { AutoresearchTaskBoard } from "../components/AutoresearchTaskBoard";
import { NavSidebar } from "../components/NavSidebar";
import { autoresearch_tasks } from "../fixtures/autoresearch_tasks";

export function AutoresearchPage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <AutoresearchTaskBoard records={autoresearch_tasks} />
          </>
        }
      />
    </SelectionProvider>
  );
}
