# ADR-FW-001 — Typed Capability Registry as Evolution Path

## Status

Proposed

## Context

The framework currently supports project generation and AI-assisted development through:

* Specs
* ADRs
* Skills
* Hooks
* `.ai/` artifacts
* Domain descriptors
* Profile-based installation

Previous specs introduced:

* `environment_profile`: `local` / `cloud`
* `capability_profile`: currently focused on `saas`
* domain-based organization under `ai/domains/`
* SaaS skills under `ai/skills/saas/`

However, the framework is progressively expanding beyond its initial Python/local/cloud scope.

Upcoming and current stack areas include:

* Python
* FastAPI
* React
* Supabase
* VPS
* Domains
* AWS
* Terraform
* Kubernetes
* Linux
* Golang
* LangGraph / LangChain ecosystem
* AI agents
* MCP
* Observability

The previous planning spec identified two options:

* Option A: keep `environment_profile` and add a flat `capabilities` list.
* Option B: replace profiles entirely with a pure flat `capabilities` list.

Option A is safer but preserves overlapping concepts.
Option B is cleaner but introduces breaking changes and may lose semantic structure as the stack grows.

The framework needs a balanced model that supports progressive adoption without forcing an immediate breaking migration.

## Decision

Adopt a  **Typed Capability Registry** .

Instead of using only a flat list of capabilities, capabilities will be organized by category.

Example:

```yaml
package_manager: uv

environment_profile: cloud

capabilities:
  languages:
    - python
    - golang

  frameworks:
    - fastapi
    - react

  cloud:
    - aws

  infrastructure:
    - terraform
    - kubernetes

  databases:
    - postgres
    - supabase

  ai:
    - langgraph
    - agents
    - mcp

  platform:
    - linux

  business:
    - saas

  operations:
    - observability
```

This model keeps backward compatibility with the current installer while creating a more scalable capability system.

## Rationale

A flat capability list works for a small framework:

```yaml
capabilities:
  - python
  - fastapi
  - aws
  - terraform
  - saas
```

But it becomes harder to reason about as the framework grows:

```yaml
capabilities:
  - python
  - golang
  - linux
  - kubernetes
  - langgraph
  - mcp
  - react
  - supabase
  - observability
```

These capabilities are not all the same kind of thing.

For example:

* Python and Golang are languages.
* FastAPI and React are frameworks.
* AWS is a cloud provider.
* Terraform and Kubernetes are infrastructure capabilities.
* Linux is a platform.
* LangGraph and MCP belong to the AI agent ecosystem.
* SaaS is a business/application model.

A typed registry preserves semantic meaning while still allowing the framework to calculate:

* which files to copy
* which dependencies to install
* which skills to include
* which hooks to enable
* which scanners to run
* which `.ai/` artifacts to generate
* which sections to include in `llms.txt`

## Compatibility Strategy

For the first migration phase, keep:

```yaml
package_manager: uv
environment_profile: local|cloud
```

These remain valid legacy fields.

Add the new typed capability model as an additional layer.

Legacy files remain valid:

```ini
package_manager=uv
environment_profile=cloud
capability_profile=saas
```

During parsing, the framework derives:

```yaml
capabilities:
  business:
    - saas
```

If the new typed capability block exists, it becomes the source of truth.

## Target Descriptor Model

Each capability will be defined under:

```text
ai/capabilities/
```

Example:

```text
ai/capabilities/
  languages/
    python.yaml
    golang.yaml

  frameworks/
    fastapi.yaml
    react.yaml

  infrastructure/
    terraform.yaml
    kubernetes.yaml

  ai/
    langgraph.yaml
    agents.yaml
    mcp.yaml

  business/
    saas.yaml
```

Each descriptor may define:

```yaml
name: fastapi
type: framework

depends_on:
  languages:
    - python

paths:
  - ai/skills/backend/fastapi.md

dependencies:
  extras:
    - fastapi
  groups:
    - dev-api

scanners:
  - python

hooks:
  - python-quality
  - api-contract-check

artifacts:
  - dependency_graph
  - context_bundle
  - llms_txt
```

## Consequences

### Positive

* Preserves compatibility with the current framework.
* Avoids forcing an immediate breaking migration.
* Scales better than a flat capability list.
* Supports future stack growth.
* Makes capability intent explicit.
* Allows better dependency resolution.
* Enables stack-aware hooks and scanners.
* Improves AI-agent context generation.

### Negative

* Slightly more complex than Option A.
* Requires a capability registry loader.
* Requires validation rules per capability type.
* Requires migration logic from legacy profile fields.
* Requires documentation so users understand capability categories.

## Migration Plan

### Phase 1 — Registry Foundation

Create:

```text
ai/runtime/capability_registry.py
ai/capabilities/
```

Support both:

```yaml
capabilities:
  - saas
```

and:

```yaml
capabilities:
  business:
    - saas
```

Flat lists are accepted temporarily and normalized internally.

### Phase 2 — Installer Integration

Update installer logic so paths are resolved from the capability registry instead of hardcoded constants.

Replace hardcoded SaaS-only logic with registry-driven path resolution.

### Phase 3 — Shared Profile Parser

Extract `.template-profile` parsing into:

```text
ai/runtime/profile.py
```

This avoids duplicated parsing logic across:

* `scripts/run_uv_sync.py`
* `scripts/hooks/sync_dependencies.py`
* future `scripts/restore_project.py`

### Phase 4 — Restore Integration

Implement:

```bash
python scripts/restore_project.py
```

The restore command should:

1. Read the active profile and capabilities.
2. Normalize legacy fields.
3. Resolve active capability descriptors.
4. Sync dependencies.
5. Regenerate skills registry.
6. Regenerate `.ai/` artifacts.
7. Regenerate `llms.txt`.
8. Validate consistency.

### Phase 5 — Multi-Stack Scanners

Introduce scanner selection by capability type.

Examples:

```yaml
languages:
  - python
  - golang

frameworks:
  - react
```

This enables:

* Python scanner
* TypeScript/React scanner
* Go scanner
* Terraform scanner
* Kubernetes manifest scanner

### Phase 6 — Gradual Deprecation

Eventually, `environment_profile` can become a derived field instead of a primary field.

For example:

```yaml
cloud:
  - aws

infrastructure:
  - terraform
```

can imply:

```yaml
environment_profile: cloud
```

But this should not be forced in the first migration.

## Decision Summary

Use  **Option C: Typed Capability Registry** .

This option combines:

* Option A's backward compatibility
* Option B's architectural clarity
* stronger long-term scalability for a growing technical stack

The framework should evolve from profile-based installation toward a typed, registry-driven capability system without breaking existing hosts immediately.

## Follow-up Specs

This ADR should lead to the following implementation specs:

1. `SPEC-FW-006` — Typed Capability Registry
2. `SPEC-FW-007` — Installer Registry Integration
3. `SPEC-FW-008` — Shared Profile Parser
4. `SPEC-FW-009` — Restore Project Command
5. `SPEC-FW-010` — Multi-Stack Scanner Pipeline
6. `SPEC-FW-011` — SaaS/Supabase/VPS/Domains Capability Expansion
7. `SPEC-FW-012` — AI Agent Ecosystem Capabilities
8. `SPEC-FW-013` — Kubernetes and Linux Capabilities
9. `SPEC-FW-014` — Golang Capability and Scanner

## Final Position

The framework should not choose between legacy profiles and pure capabilities yet.

It should adopt a typed capability registry that allows both models to coexist temporarily while preparing the framework for a future where all behavior is derived from explicit, categorized capabilities.
