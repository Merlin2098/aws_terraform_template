# Project specs

This folder is where the **host repository** writes its own specs.

The template ships this README as a placeholder. Everything else under
`specs/project/` is authored by the host project itself.

## How to add a spec

1. Copy [`../template/000-template-spec-format.md`](../template/000-template-spec-format.md) here.
2. Rename with a numbered prefix (e.g. `001-data-contract-orders.md`).
3. Fill the *Context*, *Contract*, *Invariants*, *Out of scope*,
   *References* sections.
4. Keep it short (≤ 100 lines).

## What belongs here

- Contracts specific to the host project: data contracts, pipeline
  invariants, integration boundaries, project-level decisions.

## What does not belong here

- Patterns or recipes → use `ai/skills/` (template-owned, read-only in host).
- Hard rules that apply to every project from this template → propose
  upstream in [`../template/`](../template/) or
  [`../../docs/terra_principles.md`](../../docs/terra_principles.md).
- Runbooks → keep under `docs/runbooks/` if added.
