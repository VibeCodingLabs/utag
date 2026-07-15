// generated from design.yaml component `nav-sidebar` — do not edit by hand
import React from "react";
import { NavLink } from "react-router-dom";

export function NavSidebar() {
  return (
    <nav aria-label="nav-sidebar">
      <ul style={{ listStyle: "none", padding: "var(--utag-space-2)" }}>
        <li><NavLink to="/">overview</NavLink></li>
        <li><NavLink to="/runs">runs</NavLink></li>
        <li><NavLink to="/validation">validation</NavLink></li>
        <li><NavLink to="/artifacts">artifacts</NavLink></li>
        <li><NavLink to="/registry">registry</NavLink></li>
        <li><NavLink to="/openapi">openapi</NavLink></li>
        <li><NavLink to="/mcp">mcp</NavLink></li>
        <li><NavLink to="/workflows">workflows</NavLink></li>
        <li><NavLink to="/tokens">tokens</NavLink></li>
        <li><NavLink to="/autoresearch">autoresearch</NavLink></li>
        <li><NavLink to="/ai">ai</NavLink></li>
        <li><NavLink to="/queue">queue</NavLink></li>
        <li><NavLink to="/settings">settings</NavLink></li>
      </ul>
    </nav>
  );
}
