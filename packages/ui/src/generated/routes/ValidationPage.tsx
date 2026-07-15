// generated from design.yaml route `/validation` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { SelectionProvider } from "../hooks/useInteractions";
import { ValidationReportPanel } from "../components/ValidationReportPanel";
import { SchemaValidationInspector } from "../components/SchemaValidationInspector";
import { NavSidebar } from "../components/NavSidebar";
import { schema_reports } from "../fixtures/schema_reports";
import { validation_reports } from "../fixtures/validation_reports";

export function ValidationPage() {
  return (
    <SelectionProvider>
      <ConsoleShell
        header={<strong>UTAG</strong>}
        sidebar={<NavSidebar />}
        main={
          <>
            <ValidationReportPanel records={validation_reports} />
          </>
        }
        inspector={
          <>
            <SchemaValidationInspector records={schema_reports} />
          </>
        }
      />
    </SelectionProvider>
  );
}
