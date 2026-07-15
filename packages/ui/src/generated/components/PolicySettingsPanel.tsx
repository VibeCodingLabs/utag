// generated from design.yaml component `policy-settings-panel` — do not edit by hand
import React from "react";

export type PolicySettingsPanelState = "idle";

export interface PolicySettingsPanelProps {
  resource?: string;
  state?: PolicySettingsPanelState;
  children?: React.ReactNode;
}

export function PolicySettingsPanel({ state = "idle", children }: PolicySettingsPanelProps) {
  return (
    <section role="region" aria-label="policy-settings-panel" data-state={state} tabIndex={0}
      style={{ background: "var(--utag-color-bg)", color: "var(--utag-color-fg)" }}>
      {children}
    </section>
  );
}
