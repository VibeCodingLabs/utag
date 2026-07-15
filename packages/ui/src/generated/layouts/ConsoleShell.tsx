// generated from design.yaml layout `console-shell` — do not edit by hand
import React from "react";

export interface ConsoleShellProps {
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
  main?: React.ReactNode;
  inspector?: React.ReactNode;
}

export function ConsoleShell({ sidebar, header, main, inspector }: ConsoleShellProps) {
  return (
    <div style={{ display: "grid", gridTemplateAreas: "\"sidebar\" \"header\" \"main\" \"inspector\"", gap: "var(--utag-space-2)" }}>
      <aside aria-label="sidebar" style={{ gridArea: "sidebar" }}>{sidebar}</aside>
      <header aria-label="header" style={{ gridArea: "header" }}>{header}</header>
      <main aria-label="main" style={{ gridArea: "main" }}>{main}</main>
      <aside aria-label="inspector" style={{ gridArea: "inspector" }}>{inspector}</aside>
    </div>
  );
}
