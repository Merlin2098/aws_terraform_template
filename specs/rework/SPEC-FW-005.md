# SPEC-FW-005 — Framework Refactor & Upgrade Plan

## Context

`docs/prompt/upgrade.md` asks for a complete Refactoring and Upgrade Plan covering
six challenge areas: capability-based architecture, dependency synchronization, a
`restore` mechanism, SaaS skills expansion (Supabase/VPS/Domains), `llms.txt`
integration, and a multi-stack hook system.

Three prior specs already started this effort:

- `SPEC-FW-001` — domain-based refactor, introduced `ai/domains/`.
- `SPEC-FW-002` — SaaS domain (`ai/skills/saas/`, 7 skills).
- `SPEC-FW-003` — per-domain descriptor contract (`ai/domains/*.md`).
- `SPEC-FW-004` — `capability_profile` (currently only `saas`) in `ai/installer.py`.

This spec is the architect-level plan requested by `upgrade.md`. It assesses what
SPEC-FW-001..004 already cover, analyzes remaining technical debt, and proposes a
target architecture, migration strategy, and roadmap for the rest. **It is a
planning document — it does not implement code.**

Two ADRs have since resolved the design decisions this plan originally left open:

- **`ADR-FW-001` — Typed Capability Registry.** The capability system is decided:
  a *category-typed* registry (`languages`, `frameworks`, `cloud`,
  `infrastructure`, `databases`, `ai`, `platform`, `business`, `operations`) with
  descriptors nested under `ai/capabilities/<category>/<name>.yaml`, coexisting
  with the legacy `environment_profile`/`package_manager` fields during migration.
- **`ADR-FW-002` — Standardize on UV.** `uv` is the sole supported Python package
  manager; `pip` is legacy and will not be expanded.

This spec is now **subordinate to those ADRs** — the sections below reflect their
decisions rather than presenting open options.

---

## 1. Architecture Assessment

| upgrade.md challenge | Status | Covered by |
|---|---|---|
| 1. Profile-based → capability-based architecture | Partially done | `SPEC-FW-004` added `capability_profile` (single value, only `saas`) alongside the existing `environment_profile` (local/cloud). Not yet a general capability list. |
| 2. Dependency synchronization | Partially done | `pyproject.toml` already has categorized extras (`local`, `cloud`, `saas`) and dependency groups (`dev-local`, `dev-cloud`). `scripts/hooks/sync_dependencies.py` + `scripts/run_uv_sync.py` install/sync, but only react to *existing* manifest changes — there is no regeneration or capability-driven resolution. |
| 3. Restore mechanism | Not started | No `framework restore` / `scripts/restore_project.py` exists. The closest analog is the pre-commit `ai-refresh` hook, which only regenerates `.ai/` artifacts. |
| 4. SaaS skills expansion (Supabase/VPS/Domains) | Partially done | `SPEC-FW-002` added `ai/skills/saas/auth.md` (Supabase Auth + RBAC) and `database.md` (PostgreSQL/Supabase schema). Storage, RLS detail, VPS (Docker/Nginx/SSL/Backup), and Domains (DNS/Cloudflare/SSL/Email) are not covered. |
| 5. `llms.txt` integration | Not started | `.ai/` artifacts (`context_bundle.yaml`, `skills_registry.json`, `dependencies_graph.json`, `treemap.md`) exist via `ai/tools/refresh_context.py`, but nothing generates `llms.txt`. |
| 6. Multi-stack hook system | Not started | `ai/runtime/dependency_graph.py` is Python-only (`ast`-based). No Scanner → IR → Generator separation; `_iter_python_files` and `ast.parse` are hardwired into the graph builder. |

**Existing assets to reuse (not rebuild):**

- `ai/runtime/skill_registry.py` — `build_and_persist_skills_registry` (skills index).
- `ai/runtime/context_bundle.py` — `build_and_persist_context_bundle` (project summary).
- `ai/runtime/dependency_graph.py` — `Node`/`Edge` dataclasses already model a generic graph IR; only the *scanner* (`_iter_python_files` + `ast.walk`) is Python-specific.
- `ai/tools/inspect_project.py` — language/stack detection (`_detect_languages`, `_detect_data_stack`, `_detect_cloud`).
- `ai/tools/refresh_context.py` — the existing artifact-refresh orchestrator; the natural home for a future `llms.txt` step and the natural caller of a future `restore`.
- `scripts/run_uv_sync.py` / `scripts/hooks/sync_dependencies.py` — profile-aware sync with hash-based skip and permission-error recovery.
- `ai/installer.py` — `iter_template_files`, `should_copy_*` predicates — the natural place to wire a capability registry.

---

## 2. Technical Debt Analysis

| Debt item | Location | Why it blocks upgrade.md |
|---|---|---|
| Capability set is a hardcoded literal | `ai/installer.py`: `CAPABILITY_PROFILES = {"saas"}`, `SAAS_ONLY_PATHS = {...}` | Adding `supabase`, `vps`, `domains`, `react`, `fastapi`, etc. as in the `upgrade.md` example means editing installer constants per capability — does not scale to N capabilities. |
| Two overlapping selection axes | `environment_profile` (local/cloud) + `capability_profile` (saas only) + `package_manager` (now `uv`-only per ADR-FW-002) | A project that evolves `local → cloud → saas` must re-run the installer with `--force` and re-answer the prompts; there is no single source of truth for "what does this host have." |
| Dependency sync is reactive only | `scripts/hooks/sync_dependencies.py` (`dependencies_hash`, `HASH_FILE`) | Detects manifest *changes* and re-installs, but cannot resolve the `uv sync` extras/groups from the active capability set when a capability is added or removed. |
| No restore entrypoint | — | `upgrade.md` §3 requires `framework restore` / `scripts/restore_project.py`; nothing currently re-derives skills/hooks/artifacts from the capability set after drift (e.g. manual edits to `ai/skills.yaml`, stale `.ai/`). |
| Dependency graph scanner is Python-specific | `ai/runtime/dependency_graph.py`: `_iter_python_files`, `_module_name`, `ast.parse` | The IR (`Node`/`Edge`) is already language-neutral, but `build_dependency_graph` couples scanning + IR construction in one Python-only function. Cannot add a TS/React scanner without duplicating the function. |
| `refresh_context.py` artifact set is fixed | `ai/tools/refresh_context.py`: hardcoded calls to 4 builders, `_artifact_path` requires all 4 filenames in `ai/context.yaml.artifacts` | Adding `llms.txt` (or skipping artifacts for capabilities that don't need them) requires editing this function directly; no plug-in/registration model. |
| SaaS domain has 3 of ~12 needed sub-areas | `ai/skills/saas/` (frontend, backend, database, auth, analytics, deployment, ux — 7 files) | `upgrade.md` §4 asks for Supabase (Storage, RLS detail), VPS (Docker/Nginx/SSL/Backup), Domains (DNS/Cloudflare/SSL/Email) — none exist as skills yet. |
| `.template-profile` schema is fixed at 3 lines | `ai/installer.py` `render_target_file` (TEMPLATE_PROFILE_PATH branch); read by `scripts/run_uv_sync.py::profile_from_template_file` and `scripts/hooks/sync_dependencies.py::profile_from_template_file` (duplicated logic in both files) | A capability list needs a 4th line/format, and the parsing logic is already duplicated across two scripts — a third consumer (restore) would triplicate it. |

---

## 3. Proposed Architecture

```
                ┌──────────────────────────────────┐
                │   Typed Capability Registry        │
                │   ai/capabilities/<category>/      │
                │     <name>.yaml                    │
                │   (type, depends_on, paths, deps,  │
                │    skills, scanners, hooks,        │
                │    artifacts per capability)       │
                │   loaded by                        │
                │   ai/runtime/capability_registry.py│
                │   profile read via                 │
                │   ai/runtime/profile.py (shared)   │
                └────────────┬─────────────────────────┘
                                  │ read by
        ┌─────────────────────────┼─────────────────────────┐
        │                          │                         │
┌───────▼────────┐       ┌─────────▼─────────┐     ┌─────────▼─────────┐
│  ai/installer.py │       │  scripts/restore_  │     │ ai/tools/refresh_  │
│  (host install/  │       │  project.py (NEW)  │     │ context.py (extend)│
│   re-install)    │       │  orchestrator      │     │  artifact pipeline │
└───────┬────────┘       └─────────┬─────────┘     └─────────┬─────────┘
        │                          │                         │
        │              ┌───────────┼─────────────┐           │
        │              │           │             │           │
        │       ┌──────▼─────┐ ┌───▼────────┐ ┌──▼─────────┐ │
        │       │ dependency │ │  skills    │ │  hooks     │ │
        │       │ sync/regen │ │  registry  │ │  sync      │ │
        │       │ (existing  │ │  (existing │ │ (existing  │ │
        │       │  scripts)  │ │  builder)  │ │  precommit)│ │
        │       └────────────┘ └────────────┘ └────────────┘ │
        │                                                     │
        │                          ┌──────────────────────────▼──────┐
        │                          │  Scanner Layer (per language)    │
        │                          │  python_scanner, ts_scanner, ... │
        │                          └──────────────┬───────────────────┘
        │                                         │ produces
        │                          ┌──────────────▼───────────────────┐
        │                          │  Intermediate Representation (IR) │
        │                          │  Node/Edge (already in            │
        │                          │  ai/runtime/dependency_graph.py)  │
        │                          └──────────────┬───────────────────┘
        │                                         │ consumed by
        │                          ┌──────────────▼───────────────────┐
        │                          │  Artifact Generators               │
        │                          │  context_bundle, dependency_graph, │
        │                          │  treemap, skills_registry,         │
        │                          │  llms.txt (NEW)                    │
        │                          └─────────────────────────────────────┘
        │
        └──────────────────────────────────────────────────────────────┘
              both installer and restore consult the same registry
```

**Key principles:**

- The **typed capability registry** (`ai/capabilities/<category>/<name>.yaml`,
  loaded by `ai/runtime/capability_registry.py`) is the **single source of truth**
  consumed by the installer (what to copy), restore (what to sync/regenerate), and
  the artifact pipeline (what to scan/generate). The active capability set is read
  through one shared parser (`ai/runtime/profile.py`) so installer, sync scripts,
  and restore never duplicate `.template-profile` parsing.
- The Scanner → IR → Generator split isolates language-specific code (scanners)
  from artifact logic (generators), reusing the existing `Node`/`Edge` dataclasses
  as the IR — no new data model needed.
- `restore` is an **orchestrator over existing scripts**, not a new execution
  engine — it calls `run_uv_sync.py`, `build_and_persist_skills_registry`,
  `refresh_context.refresh_context`, etc., in sequence.

---

## 4. Migration Strategy

Incremental, one subsystem per follow-up spec, following the spec sequence set by
`ADR-FW-001`, so each lands as an independently reviewable change:

1. **SPEC-FW-006 — Typed Capability Registry** (foundation for everything else).
   Introduce `ai/capabilities/<category>/<name>.yaml` descriptors and the loader
   `ai/runtime/capability_registry.py`. Migrate the existing `saas` capability
   from `SAAS_ONLY_PATHS` to a descriptor under `business/`. Accept flat legacy
   lists and normalize them internally. No behavior change for hosts.
2. **SPEC-FW-007 — Installer Registry Integration.**
   Replace `CAPABILITY_PROFILES`/`SAAS_ONLY_PATHS`/`should_copy_capability_path`
   with registry-driven path resolution. Extend `.template-profile` to carry the
   typed capability block (see Backward Compatibility below).
3. **SPEC-FW-008 — Shared Profile Parser.**
   Extract `.template-profile` parsing into `ai/runtime/profile.py`, eliminating
   the duplicated `profile_from_template_file` logic in `scripts/run_uv_sync.py`
   and `scripts/hooks/sync_dependencies.py` and giving restore a single reader.
4. **SPEC-FW-009 — Restore Project Command.**
   `scripts/restore_project.py`, orchestrating profile/capability resolution +
   `uv sync` + skills regen + artifact refresh + `llms.txt` + consistency
   validation, gated behind the registry and parser from SPEC-FW-006/007/008.
5. **SPEC-FW-010 — Multi-Stack Scanner Pipeline (+ llms.txt).**
   Extract `_iter_python_files`/`ast` scanning from `dependency_graph.py` into a
   `python_scanner`, add a minimal `ts_scanner` (package.json + import regex),
   select scanners by capability `scanners:`, and add an `llms.txt` generator
   consuming `context_bundle` + `skills_registry` + active capabilities.
6. **SPEC-FW-011 — SaaS/Supabase/VPS/Domains Capability Expansion.**
   New skills for Supabase Storage/RLS, VPS (Docker/Nginx/SSL/Backup), and
   Domains (DNS/Cloudflare/SSL/Email), each as its own capability descriptor
   per SPEC-FW-006.
7. **SPEC-FW-012..014 — Further capabilities** (per `ADR-FW-001`): AI agent
   ecosystem (LangGraph/agents/MCP), Kubernetes & Linux, and Golang capability +
   scanner. These extend the same registry/scanner machinery and are out of scope
   for the immediate roadmap below.

Each spec should land independently; SPEC-FW-006 is the hard prerequisite for
007–009 and 011, and SPEC-FW-010 can proceed in parallel.

---

## 5. Backward Compatibility Strategy

Per `ADR-FW-001`, migration is **additive and non-breaking** in its first phase:

- **`.template-profile`** — keep `package_manager=` and `environment_profile=`
  lines exactly as-is (read by `scripts/run_uv_sync.py` and
  `scripts/hooks/sync_dependencies.py`). Add a typed capability block as the new
  source of truth. The shared parser (`ai/runtime/profile.py`, SPEC-FW-008)
  reads both the legacy fields and the new block:

  ```yaml
  package_manager: uv
  environment_profile: cloud
  capabilities:
    languages: [python]
    cloud: [aws]
    infrastructure: [terraform]
    business: [saas]
  ```

- **Legacy normalization** — old `.template-profile` files keep working. When the
  typed block is absent, the parser derives capabilities from the legacy fields:
  `capability_profile=saas` → `capabilities.business: [saas]`. The first phase
  also accepts a **flat** list (`capabilities: [saas]`) and normalizes it
  internally. If the typed block is present, it becomes the source of truth.
- **`.ai/` artifacts** — remain optional and regenerable (per `ai/context.yaml`
  rule: ".ai/ is optional generated context and is never required at runtime").
  `llms.txt` follows the same rule: regenerable, not required.
- **`environment_profile` (local/cloud)** stays a valid legacy field. Per
  `ADR-FW-001` Phase 6, it may eventually become a *derived* field (e.g. `aws` +
  `terraform` present ⇒ `cloud`), but that derivation is **not forced** in the
  first migration.
- **`package_manager`** — `uv` only, per `ADR-FW-002`. The field is retained for
  legacy `.template-profile` readability but is no longer a live selection axis.

---

## 6. Folder Structure Proposal

Additions only — no existing paths move. Capability descriptors are nested by
category per `ADR-FW-001`:

```
ai/
├── capabilities/                # NEW — typed capability descriptors (SPEC-FW-006)
│   ├── languages/
│   │   └── python.yaml
│   ├── frameworks/
│   │   ├── fastapi.yaml
│   │   └── react.yaml
│   ├── cloud/
│   │   └── aws.yaml
│   ├── infrastructure/
│   │   └── terraform.yaml
│   ├── databases/
│   │   ├── postgres.yaml
│   │   └── supabase.yaml        # NEW capability (SPEC-FW-011)
│   ├── platform/
│   │   └── vps.yaml             # NEW capability (SPEC-FW-011)
│   ├── operations/
│   │   └── domains.yaml         # NEW capability (SPEC-FW-011)
│   └── business/
│       └── saas.yaml            # migrated from SAAS_ONLY_PATHS (SPEC-FW-006)
├── runtime/
│   ├── capability_registry.py   # NEW — loads ai/capabilities/**/*.yaml (SPEC-FW-006)
│   ├── profile.py               # NEW — shared .template-profile parser (SPEC-FW-008)
│   ├── scanners/                # NEW — Scanner Layer (SPEC-FW-010)
│   │   ├── python_scanner.py    #   extracted from dependency_graph.py
│   │   └── ts_scanner.py         #   new
│   └── llms_txt.py               # NEW — Generator (SPEC-FW-010)
├── skills/
│   └── saas/
│       ├── supabase_storage.md  # NEW (SPEC-FW-011)
│       ├── supabase_rls.md      # NEW (SPEC-FW-011)
│       ├── vps_docker.md        # NEW (SPEC-FW-011)
│       ├── vps_nginx_ssl.md     # NEW (SPEC-FW-011)
│       ├── vps_backup.md        # NEW (SPEC-FW-011)
│       └── domains_dns_cloudflare.md  # NEW (SPEC-FW-011)
└── domains/
    ├── supabase.md               # NEW descriptor (SPEC-FW-011), or fold into saas.md
    └── vps.md                     # NEW descriptor (SPEC-FW-011)

scripts/
└── restore_project.py            # NEW — restore orchestrator (SPEC-FW-009)

llms.txt                           # NEW — generated at host repo root (SPEC-FW-010)
```

`ai/context.yaml` gains `llms.txt` to its `artifacts:` list (per the existing
`_artifact_path` lookup pattern in `refresh_context.py`).

---

## 7. Capability System Design (Typed Capability Registry — per ADR-FW-001)

`upgrade.md` asked to "evaluate replacing profiles with a capability-based
architecture." That evaluation produced two candidate paths (additive vs. pure
replacement); **`ADR-FW-001` resolved the decision** in favor of a third,
combined option: a **Typed Capability Registry**. It keeps the backward
compatibility of the additive path and the architectural clarity of the pure
path, while adding category typing for long-term scalability. The design below
restates that decision; `ADR-FW-001` is the binding record.

### Categorized capabilities

Capabilities are organized by category rather than a flat list, because they are
not all the same kind of thing (a language vs. a framework vs. a cloud provider):

```yaml
capabilities:
  languages:      [python, golang]
  frameworks:     [fastapi, react]
  cloud:          [aws]
  infrastructure: [terraform, kubernetes]
  databases:      [postgres, supabase]
  ai:             [langgraph, agents, mcp]
  platform:       [linux]
  business:       [saas]
  operations:     [observability]
```

Categories: `languages`, `frameworks`, `cloud`, `infrastructure`, `databases`,
`ai`, `platform`, `business`, `operations`.

### Descriptor schema

Each capability is declared in `ai/capabilities/<category>/<name>.yaml`. The
descriptor carries everything the installer, restore, scanners, and artifact
generators need to act on it:

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
    - fastapi          # pyproject.toml [project.optional-dependencies]
  groups:
    - dev-api          # pyproject.toml [dependency-groups]

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

The registry (`ai/runtime/capability_registry.py`) loads all descriptors and lets
each consumer compute, from the active capability set:

- which files to copy (installer) — union of `paths`,
- which dependencies to install (restore/sync) — union of `dependencies`,
- which skills/domains to include,
- which scanners to run (Scanner Layer, §9),
- which hooks to enable,
- which `.ai/` artifacts to generate and which sections to emit in `llms.txt`.

`depends_on` lets a descriptor pull in prerequisites (e.g. `fastapi` requires
`python`), validated by category at load time.

### Replaces hardcoded installer logic

The registry replaces the literal `CAPABILITY_PROFILES = {"saas"}` and
`SAAS_ONLY_PATHS` sets in `ai/installer.py`. `should_copy_capability_path` becomes
a single membership check against the union of active capability `paths`, so new
capabilities (`supabase`, `vps`, `domains`, …) require **no installer code
change** — only a new descriptor file.

### Backward compatibility

Per §5: legacy `.template-profile` files (with `environment_profile=` /
`package_manager=` / `capability_profile=saas`) remain valid and are normalized
into the typed model (`capability_profile=saas` → `capabilities.business: [saas]`)
by the shared parser. A flat `capabilities: [saas]` list is also accepted and
normalized during the first migration phase. When the typed block is present, it
is the source of truth. `environment_profile` stays a legacy field and may become
derived later (`ADR-FW-001` Phase 6), but not in the first migration.

---

## 8. Dependency Management Design

Per `ADR-FW-002`, dependency management is **`uv`-only**. `pyproject.toml` +
`uv.lock` are the authoritative sources; `requirements.*.txt` and the `pip`
install path are **legacy** and are not expanded by this design.

**Manifest format:** reuse `pyproject.toml` `[project.optional-dependencies]`
(extras) and `[dependency-groups]` (dev groups) as the canonical manifest —
already categorized (`local`, `cloud`, `saas` extras; `dev-local`, `dev-cloud`
groups). Each new capability that has Python dependencies gets its own extra
(e.g. `supabase`, `fastapi`) following the existing pattern.

**Capability → dependency mapping:** each capability descriptor (SPEC-FW-006)
declares a `dependencies:` key naming the `pyproject.toml` extra(s)/group(s) it
requires (see the §7 descriptor schema). Example:

```yaml
# ai/capabilities/business/saas.yaml
name: saas
type: business
paths:
  - ai/skills/saas
  - ai/domains/saas.md
dependencies:
  extras: [saas]
  groups: []
skills_domain: saas
```

**Resolution workflow:**

- `uv sync` is driven by the active capability set: `scripts/run_uv_sync.py::sync_command`
  iterates the union of active capabilities' `dependencies.extras` /
  `dependencies.groups` (resolved through the shared parser, SPEC-FW-008) instead
  of the hardcoded `if profile == "cloud"` branch. Adding/removing a capability
  changes the `uv sync` extras automatically — no manifest regeneration needed,
  because `pyproject.toml` already holds every extra.
- **Restoration**: if `pyproject.toml`/`uv.lock` drift, `restore` (SPEC-FW-009)
  re-runs `uv sync` with the active capabilities' extras via the existing
  `sync_dependencies.py` (re-triggered, no new install logic). `uv.lock` is the
  reproducibility anchor.
- **Legacy `pip` hosts**: continue to consume their existing
  `requirements.*.txt` as-is. The framework does not add new logic to regenerate
  those files; migrating such hosts means adopting `uv sync` /
  `pyproject.toml` + `uv.lock` per `ADR-FW-002`.

**Hash-based skip** (`dependencies_hash` in `sync_dependencies.py`) is retained
unchanged — a no-op resolution still short-circuits via the existing hash
comparison.

---

## 9. Hook System Redesign

**Current state:** `.pre-commit-config.yaml` has two hooks —
`ai-refresh` (→ `ai/tools/refresh_context.py`) and `sync-dependencies`
(→ `scripts/hooks/sync_dependencies.py`). Both are language-agnostic at the
*hook* level; the Python-only assumption lives **inside**
`ai/runtime/dependency_graph.py::build_dependency_graph`.

**Target pipeline (SPEC-FW-010):**

```
Scanner Layer            Intermediate Representation       Artifact Generators
───────────────          ──────────────────────────        ────────────────────
python_scanner.py   ──┐                                 ┌─→ dependency_graph.json
  (ast-based, moved   │                                 │   (existing)
   from               ├─→  Node[] / Edge[]  ───────────┤
   dependency_graph)  │    (dataclasses already         ├─→ context_bundle.yaml
                       │     defined in                  │   (existing)
ts_scanner.py     ────┘     dependency_graph.py)        ├─→ treemap.md (existing)
  (NEW — package.json                                    │
   + import statements,                                  ├─→ skills_registry.json
   regex-based, no AST                                   │   (existing, separate
   dependency needed)                                    │   builder — unaffected)
                                                          │
                                                          └─→ llms.txt (NEW)
```

- `build_dependency_graph(project_root)` is split into
  `scan(project_root) -> tuple[list[Node], list[Edge], list[issue]]` per
  language, with a top-level `build_dependency_graph` that merges results from
  the selected scanners.
- **Scanner selection is capability-driven** (per the `scanners:` key in each
  descriptor, §7): the active capability set determines which scanners run
  (e.g. `python` ⇒ `python_scanner`, `react`/`fastapi` ⇒ `ts_scanner`/`python_scanner`).
  Detection via `ai/tools/inspect_project.py::_detect_languages` (already detects
  python/sql/terraform; extend with `typescript`/`javascript`) is the fallback
  when no capability registry is present, keeping behavior for legacy hosts.
  Hooks are likewise gated by the capability `hooks:` key.
- `ts_scanner.py` is intentionally minimal for v1: parse `package.json`
  `dependencies`/`devDependencies` as `external_package` nodes, and
  `import ... from "..."` / `require(...)` statements via regex (no full TS
  AST parser dependency) for internal module edges — mirrors the precision
  level of the current Python scanner without adding a new external dependency.
- `refresh_context.py::refresh_context` gains one more artifact call
  (`llms_txt.build_and_persist_llms_txt`) following the existing
  `_artifact_path` lookup pattern — purely additive, no signature changes to
  existing builders.
- `.pre-commit-config.yaml` is unchanged — both hooks already call into
  `ai/tools/refresh_context.py` and `scripts/hooks/sync_dependencies.py`, which
  absorb the new logic internally.

---

## 10. LLMs.txt Design

**Generation:** new module `ai/runtime/llms_txt.py`, mirroring the existing
`ai/runtime/context_bundle.py` shape (`build_llms_txt` /
`write_llms_txt` / `build_and_persist_llms_txt`).

**Content (sourced from existing artifacts — no new scanning):**

| Section | Source |
|---|---|
| Project summary | `context_bundle.yaml` → `project.name`, `project.purpose` |
| Architecture summary | `context_bundle.yaml` → `tech_stack`, `structure` |
| Current capabilities | `.template-profile` typed capability block, read via `ai/runtime/profile.py` (post SPEC-FW-006/007/008) |
| Relevant specifications | `specs/template/` + `specs/project/` index (file listing with titles, read from each file's first `#` heading) |
| Agent onboarding | `AGENTS.md` summary (purpose + working style sections) + `ai/domains/index.md` domain map |

**Output location:** `llms.txt` at the **host repository root** (sibling to
`AGENTS.md`/`README.md`), not inside `.ai/`, since `llms.txt` is a convention
external tools/agents look for at the repo root — but it is treated with the
same "optional, regenerable" status as `.ai/` artifacts.

**Lifecycle:**

- Regenerated by `ai/tools/refresh_context.py::refresh_context` (added to the
  existing artifact list in `ai/context.yaml`).
- Regenerated by `restore` (SPEC-FW-009) as part of "Regenerate AI artifacts".
- Not required at runtime (same rule as `.ai/` in `ai/context.yaml`); add
  `llms.txt` to `HOST_EXTRA_GITIGNORE_ENTRIES` in `ai/installer.py` if it should
  not be committed, or leave uncommitted-but-tracked if the project wants it
  visible to external tools on GitHub — **decision left to the maintainer**,
  not blocking for SPEC-FW-010.

---

## 11. Implementation Roadmap

Spec sequence per `ADR-FW-001`:

| Spec | Scope | Depends on | Est. size |
|---|---|---|---|
| SPEC-FW-006 | Typed Capability Registry (`ai/capabilities/<category>/*.yaml` + loader) | — | Small |
| SPEC-FW-007 | Installer Registry Integration (registry-driven paths, multi-capability prompt) | SPEC-FW-006 | Medium |
| SPEC-FW-008 | Shared Profile Parser (`ai/runtime/profile.py`, dedupe sync scripts) | SPEC-FW-006 | Small |
| SPEC-FW-009 | Restore Project Command (`scripts/restore_project.py`) | SPEC-FW-006, 007, 008 | Medium |
| SPEC-FW-010 | Multi-Stack Scanner Pipeline + `llms.txt` | — (independent of capability work) | Medium |
| SPEC-FW-011 | SaaS/Supabase/VPS/Domains capability expansion (skills + descriptors) | SPEC-FW-006 | Large (mostly content) |
| SPEC-FW-012..014 | AI agent ecosystem; Kubernetes & Linux; Golang capability + scanner | SPEC-FW-006, 010 | Later phases |

**Suggested order:** SPEC-FW-006 first (unblocks 007/008/009/011). SPEC-FW-010
(`llms.txt` + scanner split) can proceed in parallel — it has no dependency on
the capability work. The capability-system decision is already settled by
`ADR-FW-001`, so SPEC-FW-007 has no blocking ADR. SPEC-FW-012..014 are deferred
to later phases.

---

## 12. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Legacy host `.template-profile` files lack the typed capability block | Medium | Medium — wrong capabilities resolved | `ADR-FW-001` keeps migration additive: the shared parser normalizes legacy `environment_profile`/`capability_profile` into the typed model and also accepts a flat list during the first phase. No forced re-install. |
| Typed capability registry drifts out of sync with `ai/skills.yaml` / `ai/domains/` | Medium | Medium — agent gets inconsistent guidance | Add a `restore` validation step (SPEC-FW-009) that checks every skill in `ai/skills.yaml` maps to exactly one capability descriptor, extending the existing SPEC-FW-003 invariant ("every skill appears in exactly one domain descriptor"). |
| Category typing adds friction (users unsure which category a capability belongs to) | Medium | Low | Document categories in the registry README/loader; validate `type`/category at load time (`ADR-FW-001` "validation rules per capability type"). |
| TS/React scanner (SPEC-FW-010) produces noisy/incorrect edges with regex-based parsing | Medium | Low — affects only `dependencies_graph.json`, which is optional `.ai/` context | Keep scope minimal (package.json + top-level imports); document known limitations; do not block on full AST accuracy since `.ai/` is "never required at runtime". |
| `llms.txt` at repo root becomes another artifact to keep in sync, adding maintenance burden | Low | Low | Generate purely from existing artifacts (no new scanning); regenerated automatically by `ai-refresh` pre-commit hook, same as other `.ai/` artifacts. |
| SaaS expansion (SPEC-FW-011) grows `ai/skills/saas/` significantly, increasing agent context size for non-SaaS hosts | Low | Medium | Mitigated by registry-driven path resolution — non-`saas` hosts never receive these files. |
| Duplicated `.template-profile` parsing logic (`run_uv_sync.py` and `sync_dependencies.py`) diverges further as capabilities are added | Medium | Medium | Extract shared parsing into `ai/runtime/profile.py` (SPEC-FW-008), the single reader for installer, sync scripts, and restore. |

---

## Resolved ADRs

The architecture decisions this plan originally left open have been recorded as
ADRs in `specs/rework/` (per Global Policy 002 — ADR Before Architecture Change):

1. **Capability system** — resolved by `specs/rework/ADR-FW-001.md` (Typed
   Capability Registry). Supersedes the earlier "Option A vs. Option B" framing;
   see §7. Unblocks SPEC-FW-007.
2. **Python package manager** — resolved by `specs/rework/ADR-FW-002.md`
   (standardize on `uv`; `pip` is legacy). Drives §8.

One decision remains open but does **not** block its follow-up spec:

- **`llms.txt` commit policy** — tracked in git vs. gitignored generated
  artifact. See §10. SPEC-FW-010 defaults to gitignored (matching the `.ai/`
  precedent) until decided.

---

## Out of scope

- Implementing any of `ai/capabilities/`, `ai/runtime/capability_registry.py`,
  `ai/runtime/profile.py`, `scripts/restore_project.py`, `ai/runtime/llms_txt.py`,
  or scanner modules — these are follow-up specs (SPEC-FW-006..014).
- Modifying `ai/installer.py`, `pyproject.toml`, `.pre-commit-config.yaml`, or
  any `ai/skills/` content.
- Future SaaS capabilities explicitly deferred by `SPEC-FW-002`
  ("Future SaaS Capabilities": multi-tenant, billing, payments, notifications,
  WhatsApp, CRM, customer portal) — unaffected by this spec.

---

## References

- `docs/prompt/upgrade.md` — source brief for this spec.
- `specs/rework/ADR-FW-001.md` — Typed Capability Registry (binding decision for §3/§5/§6/§7/§9).
- `specs/rework/ADR-FW-002.md` — Standardize on UV (binding decision for §8).
- `specs/rework/SPEC-FW-001.md` — domain-based refactor (origin of `ai/domains/`).
- `specs/rework/SPEC-FW-002.md` — SaaS domain definition.
- `specs/rework/SPEC-FW-003.md` — domain descriptor contract.
- `specs/rework/SPEC-FW-004.md` — existing `capability_profile` (saas-only) in installer.
- `ai/installer.py` — `CAPABILITY_PROFILES`, `SAAS_ONLY_PATHS`, `should_copy_capability_path`.
- `ai/runtime/dependency_graph.py` — `Node`/`Edge` IR, Python-only scanner to be split.
- `ai/runtime/context_bundle.py`, `ai/runtime/skill_registry.py` — existing artifact builders to extend/reuse.
- `ai/tools/refresh_context.py` — artifact refresh orchestrator, future home of `llms.txt` generation.
- `ai/tools/inspect_project.py` — language/stack detection used for scanner selection.
- `scripts/run_uv_sync.py`, `scripts/hooks/sync_dependencies.py` — dependency sync, profile parsing to be shared.
- `pyproject.toml` — categorized dependency manifest (extras + groups).
- `.template-profile` — persisted profile/capability record.
- `ai/policies/global.md` — Policy 002 (ADR Before Architecture Change), under which ADR-FW-001/002 were recorded.
