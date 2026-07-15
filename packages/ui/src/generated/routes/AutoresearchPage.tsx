// generated from design.yaml route `/autoresearch` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { AutoresearchTaskBoard } from "../components/AutoresearchTaskBoard";

export function AutoresearchPage() {
  return (
    <ConsoleShell
      main={
        <>
        <AutoresearchTaskBoard />
        </>
      }
    />
  );
}
