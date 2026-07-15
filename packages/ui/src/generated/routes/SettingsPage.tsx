// generated from design.yaml route `/settings` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { PolicySettingsPanel } from "../components/PolicySettingsPanel";
import { NavSidebar } from "../components/NavSidebar";
import { policies } from "../fixtures/policies";

export function SettingsPage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <PolicySettingsPanel records={policies} />
          </>
        }
      />
    </SelectionProvider>
  );
}
