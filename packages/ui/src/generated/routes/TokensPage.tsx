// generated from design.yaml route `/tokens` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { DesignTokenExplorer } from "../components/DesignTokenExplorer";

export function TokensPage() {
  return (
    <ConsoleShell
      main={
        <>
        <DesignTokenExplorer />
        </>
      }
    />
  );
}
