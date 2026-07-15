// generated from design.yaml route `/ai` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { ProviderCapabilityMatrix } from "../components/ProviderCapabilityMatrix";
import { ModelCallTracePanel } from "../components/ModelCallTracePanel";
import { NavSidebar } from "../components/NavSidebar";
import { ai_providers } from "../fixtures/ai_providers";
import { model_calls } from "../fixtures/model_calls";

export function AiPage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <ProviderCapabilityMatrix records={ai_providers} />
            <ModelCallTracePanel records={model_calls} />
          </>
        }
      />
    </SelectionProvider>
  );
}
