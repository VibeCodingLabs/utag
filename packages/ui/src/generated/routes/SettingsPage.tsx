// generated from design.yaml route `/settings` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { PolicySettingsPanel } from "../components/PolicySettingsPanel";

export function SettingsPage() {
  return (
    <ConsoleShell
      main={
        <>
        <PolicySettingsPanel />
        </>
      }
    />
  );
}
