# ADR-FW-002 — Standardize Python Package Management on UV

## Status

Proposed

## Context

The framework currently maintains compatibility with multiple Python package management approaches, including support for `pip`-based workflows and `uv`-based workflows.

Historically, this compatibility required maintaining additional logic for:

* Package manager selection
* Dependency synchronization
* Requirements file generation
* Requirements file regeneration
* Installation workflows
* Environment bootstrap logic

However, all active framework development and recent projects use `uv` as the standard package management solution.

Examples include:

* ETL projects
* FastAPI applications
* SaaS applications
* AI agent projects
* Infrastructure automation tooling

Maintaining dual support for both `pip` and `uv` increases architectural complexity without providing sufficient practical value for the framework's intended use cases.

## Decision

The framework will standardize on **UV** as the sole supported Python package manager.

Effective immediately:

* `uv` becomes the official package management solution.
* New framework features will assume the presence of `uv`.
* Dependency installation and synchronization workflows will use `uv` exclusively.

The framework will no longer implement new functionality targeting `pip`.

## Consequences

### Positive

* Reduced framework complexity.
* Single dependency management workflow.
* Simplified installer logic.
* Simplified restore mechanisms.
* Simplified dependency synchronization.
* Elimination of duplicated package management code paths.
* Consistent developer experience across all projects.
* Faster environment provisioning and dependency resolution.

### Negative

* Existing hosts relying exclusively on `pip` will require migration.
* Future contributors must adopt `uv` for Python dependency management.
* Legacy `requirements.txt`-centric workflows are no longer first-class citizens.

## Migration Strategy

### Existing Projects

Projects currently using `pip` should migrate to:

```bash
uv sync
```

and adopt:

```text
pyproject.toml
uv.lock
```

as the authoritative dependency sources.

### New Projects

All newly generated projects will use:

```bash
uv init
uv add
uv remove
uv sync
```

for dependency lifecycle management.

## Scope

This ADR applies only to Python package management.

It does not introduce changes to:

* Capability architecture
* Installer architecture
* Skills
* Domains
* Hooks
* Artifact generation
* Scanner architecture
* Restore architecture

Those concerns remain governed by their respective ADRs and specifications.

## Decision Summary

The framework adopts  **UV as the single supported Python package manager** .

Support for `pip` will be considered legacy and will not be expanded in future framework development.
