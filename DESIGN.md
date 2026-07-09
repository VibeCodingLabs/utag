---
name: utag
version: alpha
colors:
  primary: "#1a1c1e"
  neutral: "#f7f5f2"
---

## Overview

utag is a typed artifact generator and provider-agnostic agent harness. Architecture: strict Pydantic IR at the center; decorator registries for generators and validators; ports (ModelPort/StructuredPort) isolate providers; a bounded validation-feedback repair loop gives identical retry semantics to instructor, pydantic-ai, and pi-RPC backends; meta-generation emits new registered generators from validated GeneratorSpecs. Generation and validation are separate composable stages. Determinism is release-gated by golden double-hash. Provenance (source, sha256) rides on every ModuleSpec. Unresolved upstream sources fail visibly, never silently.

## Colors

Documentation accent palette only; utag ships no UI. Primary (#1a1c1e) deep ink for emphasis; Neutral (#f7f5f2) warm limestone backgrounds.
