// generated from design.yaml route `/queue` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { QueueDlqPanel } from "../components/QueueDlqPanel";
import { NavSidebar } from "../components/NavSidebar";
import { jobs } from "../fixtures/jobs";

export function QueuePage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <QueueDlqPanel records={jobs} />
          </>
        }
      />
    </SelectionProvider>
  );
}
