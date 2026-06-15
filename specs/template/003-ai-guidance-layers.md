# AI guidance layers

## Context

The repository carries several kinds of guidance for the AI agent and
human contributors. This spec defines what each layer is for, where it
lives, and how to choose between them. The goal is to keep each layer
narrow and avoid duplication.

## Contract

| Layer | Path | Authoring | Tone | Lifecycle |
|---|---|---|---|---|
| **Principles** | [`docs/terra_principles.md`](../../docs/terra_principles.md) | Human, in template | Imperative ("must / never") | Slow-changing. Foundational. Template-only — not copied to host repos. |
| **Skills** | [`ai/skills/`](../../ai/skills/) | Human, in template | Recipe ("when X, do Y") | Evolves with patterns. |
| **Template specs** | [`specs/template/`](.) | Human, in template | Declarative contract | Slow. Read-only in hosts. |
| **Project specs** | [`specs/project/`](../project/) | Human, in host repo | Declarative contract | Lives in the host. |
| **Agent contract** | [`AGENTS.md`](../../AGENTS.md) | Human, in template | Operating rules for the agent | Slow. The pointer to everything. |
| **Generated context** | `.ai/` (gitignored) | Auto-refresh | Snapshot | Ephemeral. Never authoritative. |

### How to choose

- Documenting **a hard rule** ("we never enable versioning by default") →
  principle.
- Documenting **a pattern** ("how to write a Glue job") → skill.
- Documenting **what is true about this template** ("the artifact bucket
  always has AES256") → template spec.
- Documenting **what is true about this host project** ("orders pipeline
  reads from `s3://acme-raw/orders/`") → project spec.
- Telling the agent **how to behave** (working style, approval boundaries)
  → `AGENTS.md`.

### Discoverability

- The agent reads `AGENTS.md` first; it points to the other layers.
- [`ai/skills.yaml`](../../ai/skills.yaml) indexes skills.
- [`ai/context.yaml`](../../ai/context.yaml) lists guidance roots,
  including `specs/template/` and `specs/project/` when present.
- `specs/README.md` is the entry point for human readers of this folder.

## Invariants

- A given fact lives in exactly one layer. If you find yourself copying a
  rule from `terra_principles.md` into a spec, link instead.
- `specs/template/` is never edited in a host repo; changes go upstream.
- `specs/project/` is never edited from the template; it is host-owned.
- Skills do not contain contracts; specs do not contain recipes.

## Out of scope

- Runbooks (operational procedures) — when added, they live under
  `docs/runbooks/`, not in `specs/` or `ai/skills/`.
- ADRs (architectural decisions) — when added, they live under
  `docs/adr/`, capturing *why* a decision was taken; specs capture *what*
  the contract is.

## References

- [`AGENTS.md`](../../AGENTS.md)
- [`docs/terra_principles.md`](../../docs/terra_principles.md)
- [`ai/skills.yaml`](../../ai/skills.yaml), [`ai/context.yaml`](../../ai/context.yaml)
- [`specs/README.md`](../README.md)
