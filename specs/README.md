# Specs

Specs are **project contracts**: short, durable documents that state what is
true, expected, or invariant about a piece of this repository. They are
source-of-truth for both humans and the AI agent.

This folder is **only present in cloud-profile installations** of the
template. Local-profile hosts do not have a `specs/` folder.

## Layout

```
specs/
├── template/   # contracts inherited from the template (read-only in hosts)
└── project/    # contracts written by the host repo for its own project
```

- **`specs/template/`** — Authored by the template. In a host repo, this
  folder is gitignored (read-only) and refreshed by re-running the
  installer. Do not edit these files in a host repo; propose changes
  upstream in the template.
- **`specs/project/`** — Empty in the template (placeholder only). The host
  repo writes its own specs here, following
  [`template/000-template-spec-format.md`](template/000-template-spec-format.md).

## Spec vs. skill vs. principle

| Layer | Purpose | Tone | Where |
|---|---|---|---|
| Spec | Contract: what is true / expected / invariant | declarative | `specs/` |
| Skill | Pattern: how to do X well | recipe | `ai/skills/` |
| Principle | Hard rule: must / must-not | imperative | `docs/terra_principles.md` |

If you are documenting a *pattern* or *example*, write a skill. If you are
fixing an *invariant* of the project, write a spec. They do not overlap.

## Index of template specs

- [`template/000-template-spec-format.md`](template/000-template-spec-format.md) — reusable format for new specs
- [`template/001-template-contract.md`](template/001-template-contract.md) — what the template provides and expects
- [`template/002-infra-baseline.md`](template/002-infra-baseline.md) — invariants of `infra/`
- [`template/003-ai-guidance-layers.md`](template/003-ai-guidance-layers.md) — how skills, specs, principles relate

## How to add a host project spec

1. Copy [`template/000-template-spec-format.md`](template/000-template-spec-format.md) into `specs/project/` with a numbered name (e.g. `001-data-contract-orders.md`).
2. Fill the *Context*, *Contract*, *Invariants*, *Out of scope*, *References* sections.
3. Keep it short (≤ 100 lines). If it grows, split it.
4. Commit and reference it from PRs that change the contract.
