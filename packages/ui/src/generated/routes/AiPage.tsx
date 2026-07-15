// generated from design.yaml route `/ai` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { ModelCallTracePanel } from "../components/ModelCallTracePanel";
import { ProviderCapabilityMatrix } from "../components/ProviderCapabilityMatrix";

export function AiPage() {
  return (
    <ConsoleShell
      main={
        <>
        <ProviderCapabilityMatrix />
        <ModelCallTracePanel />
        </>
      }
    />
  );
}
