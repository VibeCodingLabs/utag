// generated route table from design.yaml — do not edit by hand
import React from "react";
import { HomePage } from "./HomePage";
import { RunsPage } from "./RunsPage";
import { ValidationPage } from "./ValidationPage";
import { ArtifactsPage } from "./ArtifactsPage";
import { RegistryPage } from "./RegistryPage";
import { OpenapiPage } from "./OpenapiPage";
import { McpPage } from "./McpPage";
import { WorkflowsPage } from "./WorkflowsPage";
import { TokensPage } from "./TokensPage";
import { AutoresearchPage } from "./AutoresearchPage";
import { AiPage } from "./AiPage";
import { QueuePage } from "./QueuePage";
import { SettingsPage } from "./SettingsPage";

export const routes = [
  { path: "/", element: <HomePage /> },
  { path: "/runs", element: <RunsPage /> },
  { path: "/validation", element: <ValidationPage /> },
  { path: "/artifacts", element: <ArtifactsPage /> },
  { path: "/registry", element: <RegistryPage /> },
  { path: "/openapi", element: <OpenapiPage /> },
  { path: "/mcp", element: <McpPage /> },
  { path: "/workflows", element: <WorkflowsPage /> },
  { path: "/tokens", element: <TokensPage /> },
  { path: "/autoresearch", element: <AutoresearchPage /> },
  { path: "/ai", element: <AiPage /> },
  { path: "/queue", element: <QueuePage /> },
  { path: "/settings", element: <SettingsPage /> },
];
