// generated fixtures for resource `autoresearch-tasks` (autoresearch-task) — do not edit by hand
import type { AutoresearchTask } from "../schemas/contracts";

export const autoresearch_tasks: AutoresearchTask[] = [
  {
    "done_when": [
      "all_gates_pass"
    ],
    "gates": [
      {
        "command": "python scripts/validate_schemas.py --root .",
        "name": "schema"
      }
    ],
    "goal": "Generate the observability dashboard from design.yaml and validate it.",
    "id": "ar-ui-observability-dashboard",
    "inputs": [
      "design.yaml"
    ],
    "mode": "implement",
    "required_outputs": [
      "packages/ui/src/generated/components/RunTimeline.tsx"
    ]
  },
  {
    "done_when": [
      "all_gates_pass"
    ],
    "gates": [
      {
        "command": "python scripts/validate_schemas.py --root .",
        "name": "schema"
      }
    ],
    "goal": "Generate the observability dashboard from design.yaml and validate it.",
    "id": "ar-ui-observability-dashboard-2",
    "inputs": [
      "design.yaml"
    ],
    "mode": "implement",
    "required_outputs": [
      "packages/ui/src/generated/components/RunTimeline.tsx"
    ]
  },
  {
    "done_when": [
      "all_gates_pass"
    ],
    "gates": [
      {
        "command": "python scripts/validate_schemas.py --root .",
        "name": "schema"
      }
    ],
    "goal": "Generate the observability dashboard from design.yaml and validate it.",
    "id": "ar-ui-observability-dashboard-3",
    "inputs": [
      "design.yaml"
    ],
    "mode": "implement",
    "required_outputs": [
      "packages/ui/src/generated/components/RunTimeline.tsx"
    ]
  }
];
