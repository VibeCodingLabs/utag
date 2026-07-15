// generated from design.yaml route `/queue` — do not edit by hand
import React from "react";
import { ConsoleShell } from "../layouts/ConsoleShell";
import { QueueDlqPanel } from "../components/QueueDlqPanel";

export function QueuePage() {
  return (
    <ConsoleShell
      main={
        <>
        <QueueDlqPanel />
        </>
      }
    />
  );
}
