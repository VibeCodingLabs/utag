// generated from design.yaml route `/validation` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { ValidationReportPanel } from "../components/ValidationReportPanel";

export function ValidationPage() {
  return (
    <ConsoleShell
      main={
        <>
        <ValidationReportPanel />
        </>
      }
    />
  );
}
