// generated from design.yaml data.contracts — do not edit by hand
export interface AIProviderManifest {
  extensions?: Record<string, unknown> | null;
  id: string;
  name: string;
  models?: ModelCapability[];
  env_credentials?: string[];
}

export interface ArtifactManifest {
  extensions?: Record<string, unknown> | null;
  id: string;
  target: string;
  files: FileDigest[];
  provenance: ArtifactProvenance;
  deterministic?: boolean;
}

export interface ArtifactProvenance {
  extensions?: Record<string, unknown> | null;
  generator_id: string;
  utag_version: string;
  source_paths: string[];
  inputs_sha256: string;
}

export interface AutoresearchPlan {
  extensions?: Record<string, unknown> | null;
  task_id: string;
  steps: AutoresearchStep[];
}

export interface AutoresearchStep {
  extensions?: Record<string, unknown> | null;
  id: string;
  kind: "research" | "plan" | "schema" | "tests" | "implementation" | "validation" | "docs" | "receipt";
  description: string;
  status?: "pending" | "running" | "done" | "failed";
}

export interface AutoresearchTask {
  extensions?: Record<string, unknown> | null;
  id: string;
  goal: string;
  mode: "research" | "implement" | "dry-run";
  inputs?: string[];
  required_outputs?: string[];
  gates?: TaskGate[];
  done_when?: string[];
}

export interface CssVariable {
  extensions?: Record<string, unknown> | null;
  name: string;
  value: string;
}

export interface CssVariableManifest {
  extensions?: Record<string, unknown> | null;
  file: string;
  variables: CssVariable[];
  source_design: string;
}

export interface FileDigest {
  extensions?: Record<string, unknown> | null;
  path: string;
  sha256: string;
  bytes: number;
}

export interface GeneratorManifest {
  extensions?: Record<string, unknown> | null;
  id: string;
  name: string;
  version: string;
  kind?: "generator";
  input_schema?: string | null;
  output_schema?: string | null;
  output_files?: string[];
  required_capabilities?: string[];
  optional_capabilities?: string[];
  side_effects?: string[];
  risk_level?: "low" | "medium" | "high";
  deterministic?: boolean;
  validation_gates?: string[];
  test_files?: string[];
  entrypoints?: string[];
  owner?: string;
  status?: "implemented" | "experimental" | "planned" | "deprecated";
}

export interface MCPToolContract {
  extensions?: Record<string, unknown> | null;
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  output_schema?: Record<string, unknown> | null;
  side_effect: "none" | "read" | "write" | "destructive" | "network";
  auth_scopes?: string[];
  policy_status?: "allowed" | "denied" | "review";
}

export interface MetricPoint {
  extensions?: Record<string, unknown> | null;
  name: string;
  value: number;
  labels?: Record<string, string>;
}

export interface ModelCallTrace {
  extensions?: Record<string, unknown> | null;
  run_id: string;
  provider: string;
  model: string;
  prompt_sha256: string;
  output_sha256: string;
  input_tokens?: number | null;
  output_tokens?: number | null;
  cost_usd?: number | null;
  latency_ms?: number | null;
}

export interface ModelCapability {
  extensions?: Record<string, unknown> | null;
  id: string;
  context_tokens: number;
  output_tokens: number;
  structured_output?: boolean;
  tool_call?: boolean;
  reasoning?: boolean;
}

export interface ModelRouterPolicy {
  extensions?: Record<string, unknown> | null;
  task_kind: string;
  max_cost_usd?: number | null;
  max_latency_ms?: number | null;
  require_structured_output?: boolean;
  local_only?: boolean;
  no_network?: boolean;
  allow_fallback?: boolean;
  prefer_cached?: boolean;
}

export interface OpenApiOperation {
  extensions?: Record<string, unknown> | null;
  operation_id: string;
  method: "get" | "put" | "post" | "delete" | "options" | "head" | "patch" | "trace";
  path: string;
  summary?: string;
  tags?: string[];
  has_request_schema?: boolean;
  has_response_schema?: boolean;
}

export interface RunSpan {
  extensions?: Record<string, unknown> | null;
  span_id: string;
  name: string;
  start_ms: number;
  end_ms: number;
  parent_span_id?: string | null;
  attributes?: Record<string, string>;
}

export interface RunTrace {
  extensions?: Record<string, unknown> | null;
  run_id: string;
  spans?: RunSpan[];
}

export interface TaskGate {
  extensions?: Record<string, unknown> | null;
  name: string;
  command: string;
}

export interface ValidationFinding {
  extensions?: Record<string, unknown> | null;
  severity: "info" | "warn" | "error";
  code: string;
  message: string;
  path?: string | null;
  pointer?: string | null;
}

export interface ValidationReport {
  extensions?: Record<string, unknown> | null;
  artifact_id: string;
  valid: boolean;
  findings?: ValidationFinding[];
  run_id?: string | null;
  span_id?: string | null;
}

export interface WorkerJobTrace {
  extensions?: Record<string, unknown> | null;
  job_id: string;
  status: "queued" | "running" | "completed" | "failed" | "dead-letter";
  run_id?: string | null;
}
