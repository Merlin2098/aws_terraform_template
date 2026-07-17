# ADR-FW-004 — Workspace Framework: Reference Model, pip, Multi-Repo Support

**Status:** Accepted
**Supersedes:** ADR-FW-003 (copy-based distribution with content-hash drift detection),
               SPEC-FW-015 (uv-only dependency management)
**Date:** 2026-06-23

---

## Context

ADR-FW-003 established a **copy-based distribution model**: the framework copies its
artifact tree into every host repository and uses per-file SHA-256 hashes + a tree
digest to detect divergence between template and host. SPEC-FW-015 locked the
framework to `uv` as the sole Python dependency manager.

Both decisions were explicitly sound for the original scope (single isolated host
repo, data-engineering AWS template). They become constraints under the new scope:

1. **Multiple repositories** — `WuilioOSbackend` (FastAPI/pip) and `wuilio4pl`
   (Next.js/npm) must consume the same guidance without each hosting a copy of `ai/`,
   `scripts/`, and `AGENTS.md`. The copy model creates three independent copies that
   diverge immediately (different AGENTS.md domains, different managers).

2. **Heterogeneous package managers** — pip and npm hosts cannot absorb `uv.lock` /
   `[dependency-groups]` without conflict. The uv-only constraint blocks every
   non-Python repo from adopting the framework.

3. **Upgrade churn** — each `--update` run risks `locally-modified` / `conflict`
   classifications on files the host legitimately owns. Re-pinning a version becomes
   a multi-file PR instead of a one-line pointer change.

4. **Workspace context** — the sibling repos live under a shared umbrella
   (`Wuillio/`). A workspace-level `CLAUDE.md` and manifest already exist implicitly
   (backend README references `../CLAUDE.md`). Formalising this layer requires a
   distribution model that does not require each repo to own a full copy of the tree.

---

## Decision

Replace the copy-installer with a **reference model**:

### 1. Installable package

`agents_template` is repackaged as `agents_framework` — a pip-installable Python
package. Framework resources (capabilities, skills, policies, domains, context
config, spec templates) ship as **package-data** co-located with the Python package.
The engine accesses its own data via `framework_root()` (`Path(__file__).parent`),
not via a caller-supplied `template_root`.

### 2. Distribution: git submodule (vendored, SHA-pinned)

The workspace umbrella (`Wuillio/`) carries `agents_template` as a git submodule at
`vendor/agents-framework`. Each Python host installs it editably:

```
pip install -e vendor/agents-framework
```

The Node host (`wuilio4pl`) installs it as an isolated CLI tool:

```
pipx install ./vendor/agents-framework
```

Upgrade = `git submodule update --remote` + re-pin SHA in the umbrella. Zero file
churn in host repos.

### 3. Per-repo attachment via `.agents-framework.yaml` (schema v2)

Each participating repo opts in with a single config file. The engine reads this
file to resolve active capabilities, skills, and policies. The host's own
`CLAUDE.md` and `AGENTS.md` are never touched by the framework.

### 4. pip replaces uv for host dependency management

`pip_install_args(resolved)` replaces `uv_sync_args()` as the canonical function
for generating install commands from resolved capabilities. Hosts with `uv`
can still use it — `dependencies.manager` in `.agents-framework.yaml` governs
which tool is invoked. The framework's own development environment remains
`uv`-managed internally; only the **host integration** switches to pip-first.

PEP 735 `[dependency-groups]` are mapped to extras or a separate
`requirements-dev.txt` for pip compatibility.

### 5. `agents-framework` CLI replaces hooks / installer scripts

| Old | New |
|---|---|
| `install_windows.py`, `install_linux.py` | removed |
| `scripts/restore_project.py` | removed |
| `ai/installer.py` (copy + manifest + drift) | removed |
| `scripts/hooks/ai_refresh.py` | `agents-framework ai-refresh` |
| `scripts/hooks/sync_dependencies.py` | `agents-framework sync-deps` |
| `make ai-refresh` | `agents-framework ai-refresh` |

### 6. Workspace anchor

`Wuillio/` becomes a git umbrella repo containing:
- `workspace.yaml` — member registry
- `CLAUDE.md` — shared cross-repo guidance + precedence rules
- `vendor/agents-framework` — the submodule

Member repos remain independent git repos; they are listed in `workspace.yaml`
by path, not converted to submodules.

---

## Precedence hierarchy (multi-CLAUDE.md)

Claude Code concatenates `CLAUDE.md` files from `cwd` upward. The root
`CLAUDE.md` declares the tie-breaking rule.

**Eje A — Conventions/patterns → most specific wins (host):**
1. Repo `CLAUDE.md` + repo `.claude/` — max authority
2. Repo `AGENTS.md`
3. Repo `specs/project/`
4. Repo `.agents-framework.yaml` → `overrides`
5. Workspace `CLAUDE.md` + `workspace.yaml` shared overrides
6. Framework `skills/` + `domains/`
7. Framework `specs/template/` — minimum (defaults)

**Eje B — Security/approval (required policies) → framework wins:**
1. Framework `required` policies for active capabilities (Policies 002, 003, 004,
   007, 009, 010) — cannot be relaxed from a host repo
2. A host may only remove a required policy by **disabling the capability**
3. A host may always **tighten**, never loosen

**Rule:** Is it security/approval? → Axis B. Otherwise → Axis A (most specific wins).

---

## Consequences

### Positive
- Zero file injection into host repos (no `ai/`, `scripts/`, `AGENTS.md` copies).
- Upgrade = one-line SHA pin; no drift classification needed.
- Heterogeneous stack support: pip hosts, npm hosts, and future stacks can all
  consume guidance via the CLI without touching their dependency files.
- The engine (`ai/runtime/`) is now a proper importable library with no `sys.path`
  manipulation or `parents[N]` gymnastics.
- The copy-installer test suite (≈3 test files, ≈600 lines) can be retired.

### Negative / trade-offs
- Requires `pip install -e vendor/agents-framework` (or `pipx`) in each host
  environment. This is a new manual step vs the old "copy and run" model.
- The workspace umbrella being a git repo complicates nested-repo workflows
  (git operations must specify which repo). Documented in `CLAUDE.md`.
- The submodule pointing to `Merlin2098/aws_terraform_template` (personal account)
  rather than the `WuilioWS` org requires either a fork/transfer or documented
  cross-account access. Tracked as an open item.

### Out of scope (not changed by this ADR)
- Converting `WuilioOSbackend` or `wuilio4pl` to git submodules.
- Promoting `wuilio4pl/.claude/agents/` to the shared layer (separate ADR/PR).
- Cryptographic signing or semantic drift analysis (deferred by ADR-FW-003,
  remains deferred).

---

## Implementation references

- `agents_framework/` — new package root (replaces `ai/` Python modules)
- `agents_framework/cli.py` — CLI entry point
- `agents_framework/workspace.py` — workspace-level commands
- `agents_framework/runtime/` — adapted engine modules
- `Wuillio/workspace.yaml` — workspace manifest
- `Wuillio/CLAUDE.md` — umbrella guidance
- `WuilioOSbackend/.agents-framework.yaml` — backend attachment
- `wuilio4pl/.agents-framework.yaml` — frontend attachment
