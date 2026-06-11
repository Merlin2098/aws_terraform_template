# SPEC-FW-IMPL-PLAN — Framework Refactor Program: Implementation Plan

> **Status**: Proposed
> **Type**: Implementation plan (not a spec; does not introduce new behavior)
> **Produced from**: `docs/prompt/implement.md`, analyzing all of `specs/rework/`

This document is the execution roadmap for turning the approved `specs/rework/`
documents (SPEC-FW-001..005, ADR-FW-001, ADR-FW-002, and the SPEC-FW-006..014
sequence they define) into changes to the framework codebase. It does not
implement code, modify files, or generate patches. It is the input for
specification-by-specification execution.

---

## 1. Executive Summary

The framework has fully specified — but not yet built — its next architectural
generation: a **typed, category-based capability registry** (`ADR-FW-001`)
combined with **uv as the sole Python package manager** (`ADR-FW-002`). Today's
codebase still runs on the previous generation: a flat `environment_profile` /
`package_manager` / `capability_profile` triple, hardcoded in
`ai/installer.py` (`CAPABILITY_PROFILES`, `SAAS_ONLY_PATHS`), with `pip` and
`uv` paths coexisting in `scripts/run_pip_init.py`,
`scripts/run_uv_sync.py`, and `scripts/hooks/sync_dependencies.py`.

`SPEC-FW-001` through `SPEC-FW-005` are implemented and form a stable base:
domain descriptors (`ai/domains/`), the SaaS domain and skills
(`ai/skills/saas/`), the skill/domain descriptor contract, and the
capability-profile installer mechanics. `SPEC-FW-004` and `SPEC-FW-005` have
already been reconciled (in this working tree) to point at `ADR-FW-001` /
`ADR-FW-002` as the binding direction, so this plan builds directly on their
current (post-reconciliation) content — particularly SPEC-FW-005 §4, §7, §11.

Nothing in `SPEC-FW-006..014` exists yet: there is no `ai/capabilities/`, no
`ai/runtime/capability_registry.py`, no `ai/runtime/profile.py`, no
`scripts/restore_project.py`, and no `llms.txt`. The framework is in a
"specs approved, nothing built" state.

**Guiding principles for the program** (directly from `implement.md` and the
ADRs):

- **Additive first.** The typed capability registry (`SPEC-FW-006`) and the
  shared profile parser (`SPEC-FW-008`) are pure additions — new files, no
  existing behavior changes — and should land before anything that changes
  `ai/installer.py` or sync scripts.
- **Legacy stays parseable.** `.template-profile` files using
  `package_manager=` / `environment_profile=` / `capability_profile=saas`
  must continue to parse correctly throughout the program (per ADR-FW-001's
  Compatibility Strategy).
- **uv-only is a precondition, not a phase deliverable.** ADR-FW-002 mostly
  *removes* future work (no new pip features) rather than *adding* it; its
  main implementation cost is deciding how far to retire `run_pip_init.py`
  and `requirements.*.txt`, which this plan treats as a small, isolated Phase 0
  decision rather than entangling it with the registry work.
- **Reuse existing IR and artifact patterns.** `ai/runtime/dependency_graph.py`
  already has a neutral `Node`/`Edge` IR; `ai/tools/refresh_context.py` already
  has an artifact-path resolution pattern (`_artifact_path`); `ai/installer.py`
  already has path-filtering predicates (`should_copy_*`). New subsystems
  (registry, scanners, restore) should extend these patterns, not invent
  parallel ones.
- **`SPEC-FW-006` is the foundation.** Every other new spec (007, 008, 009,
  011, and transitively 012-014) depends on the typed capability registry
  existing. It is both the lowest-risk (purely additive) and highest-leverage
  spec to implement first.

---

## 2. Specification Dependency Graph

### 2.1 Graph

```text
ADR-FW-002 (uv-only)  ─────────────┐  (transversal precondition;
                                    │   simplifies 008/009, retires
                                    │   pip-only code paths)
                                    ▼
SPEC-FW-006 (Typed Capability Registry)
   │
   ├──────────────► SPEC-FW-008 (Shared Profile Parser)
   │                       │
   │                       ▼
   ├──────────────► SPEC-FW-007 (Installer Registry Integration)
   │                       │
   │                       ▼
   │                SPEC-FW-009 (Restore Project Command)
   │
   ├──────────────► SPEC-FW-011 (SaaS/Supabase/VPS/Domains Expansion)
   │                       │
   │                       ▼
   │                SPEC-FW-012 (AI Agent Ecosystem Capabilities)
   │                       │
   │                       ▼
   │                SPEC-FW-013 (Kubernetes and Linux Capabilities)
   │                       │
   │                       ▼
   │                SPEC-FW-014 (Golang Capability and Scanner)
   │
   └──────────────► SPEC-FW-010 (Multi-Stack Scanner Pipeline + llms.txt)
                            ▲
                            │ (independent of 007/008/009;
                            │  only needs 006's descriptor
                            │  shape for `scanners:`/`artifacts:` keys)
                       (no other dependencies)
```

Key relationships:

- **SPEC-FW-006** is the single root. Nothing else in 007-014 can be
  meaningfully implemented before it, because every later spec consumes the
  typed descriptor model (`ai/capabilities/<category>/<name>.yaml`) and/or the
  registry loader.
- **SPEC-FW-008** depends only on 006 (it needs the normalized profile shape
  the registry defines). It does **not** depend on 007.
- **SPEC-FW-007** depends on both 006 (descriptor model) and 008 (shared
  parser) — the installer should call the shared parser rather than
  reimplement `.template-profile` parsing a third time.
- **SPEC-FW-009** depends on 006, 007, and 008: restore re-reads the profile
  (008), resolves capabilities (006), and needs the installer's path-resolution
  logic to already be registry-driven (007) so restore and install share one
  source of truth.
- **SPEC-FW-010** depends on 006 only, and only loosely (it needs descriptors
  to expose `scanners:` and `artifacts:` keys so the pipeline can be
  capability-driven from day one). It can be built in parallel with 007/008/009
  by a different workstream.
- **SPEC-FW-011** depends on 006 (it is primarily new descriptors + skill
  content under the `business`/`databases`/`platform` categories). It does not
  require 007 to be *content-complete*, but the new paths it adds will only be
  *delivered to hosts* once 007 makes the installer registry-driven — so 011's
  descriptors can be authored in parallel with 007, but its end-to-end
  validation depends on 007.
- **SPEC-FW-012, 013, 014** each depend on 006 (descriptor model) and 010
  (scanner pipeline, since each adds a new scanner: AI/agents, Kubernetes/Linux,
  Go). They are independent of each other and can be sequenced in any order
  among themselves.
- **ADR-FW-002 (uv-only)** is not a spec and has no dependents in the graph
  above, but it touches the same files as 008 and 009
  (`scripts/run_uv_sync.py`, `scripts/hooks/sync_dependencies.py`,
  `scripts/run_pip_init.py`). Doing its cleanup *before* 008 means 008 extracts
  a parser from fewer, simpler call sites.

### 2.2 Specs touching the same files

| File | Specs that touch it |
|---|---|
| `ai/installer.py` | 004 (already implemented), 006 (reads new registry), 007 (core rewrite), 011 (new SAAS-adjacent paths to filter) |
| `scripts/run_uv_sync.py` | ADR-FW-002 (pip-path removal), 008 (extract `profile_from_template_file`) |
| `scripts/hooks/sync_dependencies.py` | ADR-FW-002 (pip-path removal), 008 (extract `profile_from_template_file`/`resolve_profile`), 009 (restore calls into sync) |
| `scripts/run_pip_init.py` | ADR-FW-002 (deprecate or remove) |
| `ai/runtime/dependency_graph.py` | 010 (extend `Node`/`Edge` IR for non-Python languages) |
| `ai/tools/refresh_context.py` | 009 (restore calls `refresh_context`), 010 (new `llms_txt` artifact + new scanners wired into `_artifact_path`) |
| `ai/context.yaml` | 010 (new `llms.txt` artifact entry, new `treemap_ignore_dirs`/scanner config per language) |
| `ai/skills.yaml` | 011, 012, 013, 014 (new skill entries per new capability) |
| `ai/domains/index.md` | 011, 012, 013, 014 (new domain links, same pattern as `ai/domains/saas.md` today) |
| `pyproject.toml` | ADR-FW-002 (extras/groups cleanup), 011/012/013/014 (new optional dependency groups per capability) |
| `.template-profile` | 006 (new typed `capabilities:` block, additive), 008 (parsed by shared parser) |

---

## 3. Current State Assessment

| Spec / ADR | Status | Evidence |
|---|---|---|
| **SPEC-FW-001** | Implemented | `ai/domains/` exists with `index.md`, `aws.md`, `data-product.md`, `frontend.md`, `python.md`, `saas.md`, `terraform.md`. |
| **SPEC-FW-002** | Implemented | `ai/skills/saas/` contains `analytics.md`, `auth.md`, `backend.md`, `database.md`, `deployment.md`, `frontend.md`, `ux.md`; `ai/domains/saas.md` exists. |
| **SPEC-FW-003** | Implemented | `ai/skills.yaml` registry + `ai/runtime/skill_registry.py` build the descriptor-to-skill mapping described by the spec. |
| **SPEC-FW-004** | Implemented, partially superseded | `ai/installer.py` has `CAPABILITY_PROFILES = {"saas"}`, `SAAS_ONLY_PATHS`, `prompt_capability_profile`, `validate_capability_profile`, `should_copy_capability_path`, and writes `capability_profile=` to `.template-profile` — exactly as SPEC-FW-004 describes. The spec itself now carries a supersession note pointing at ADR-FW-001/002 as the binding direction for the *next* iteration of this mechanism. |
| **SPEC-FW-005** | Implemented (as a planning spec); reconciled | Already updated in this working tree to reference ADR-FW-001/002 as resolved decisions; its §4/§7/§11 define the SPEC-FW-006..014 sequence used by this plan. |
| **ADR-FW-001 (Typed Capability Registry)** | Not Implemented | No `ai/capabilities/` directory, no `ai/runtime/capability_registry.py`, no `ai/runtime/profile.py`. Confirmed via `git ls-files` and directory listing. |
| **ADR-FW-002 (uv-only)** | Implemented | `pyproject.toml` (with `[project.optional-dependencies]` and `[dependency-groups]`) and `uv.lock` are authoritative for `uv sync`; `scripts/run_uv_sync.py` is the only sync path. SPEC-FW-015 (Phase 7) removed `scripts/run_pip_init.py`, root `requirements*.txt`, and the `package_manager` (`pip`\|`uv`) axis from `ai/installer.py` and `scripts/hooks/sync_dependencies.py`. `ai/runtime/profile.py`/`scripts/restore_project.py` retain documented legacy `package_manager=pip` read/warning carve-outs. |
| **SPEC-FW-006 (Typed Capability Registry)** | Not Implemented | — |
| **SPEC-FW-007 (Installer Registry Integration)** | Not Implemented | — |
| **SPEC-FW-008 (Shared Profile Parser)** | Not Implemented | `profile_from_template_file` is duplicated verbatim (with a slightly different `ENVIRONMENT_PROFILES`-only scope) in `scripts/run_uv_sync.py` and `scripts/hooks/sync_dependencies.py`; `ai/installer.py` writes `.template-profile` but no module reads the full triple back. |
| **SPEC-FW-009 (Restore Project Command)** | Not Implemented | No `scripts/restore_project.py`. |
| **SPEC-FW-010 (Multi-Stack Scanner Pipeline)** | Not Implemented | `ai/runtime/dependency_graph.py` is Python-only (`_iter_python_files`, `ast`-based). No `llms.txt` generator. |
| **SPEC-FW-011 (SaaS/Supabase/VPS/Domains Expansion)** | Not Implemented | `ai/skills/saas/` has 7 generic files; no Supabase-, VPS-, or domain/DNS-specific skill content or descriptors. |
| **SPEC-FW-012 (AI Agent Ecosystem Capabilities)** | Not Implemented | No LangGraph/agents/MCP descriptors or skills. |
| **SPEC-FW-013 (Kubernetes and Linux Capabilities)** | Not Implemented | `scripts/linux/` exists (shell setup scripts) but is not descriptor- or capability-driven; no Kubernetes content. |
| **SPEC-FW-014 (Golang Capability and Scanner)** | Not Implemented | No Go descriptors, skills, or scanner. |
| **SPEC-FW-015 (Pip Legacy Retirement)** | Implemented | `pip`/`requirements*.txt` code paths removed from `ai/installer.py`, `scripts/hooks/sync_dependencies.py`, `install_linux.py`/`install_windows.py`, `scripts/package.py`; `scripts/run_pip_init.py` and root `requirements*.txt` deleted. `ai/runtime/profile.py` and `scripts/restore_project.py` retain documented compatibility carve-outs (legacy `package_manager=pip` parsing + migration warning). |

---

## 4. Gap Analysis

For each not-yet-implemented spec: what's missing, what existing code should be
**reused** (not rewritten), and any architectural conflicts to resolve.

### SPEC-FW-006 — Typed Capability Registry

- **Missing**: `ai/capabilities/<category>/<name>.yaml` directory tree (per
  ADR-FW-001's 9 categories: `languages`, `frameworks`, `cloud`,
  `infrastructure`, `databases`, `ai`, `platform`, `business`, `operations`);
  `ai/runtime/capability_registry.py` loader that parses descriptors and
  exposes a normalized in-memory model; normalization logic for legacy flat
  `capabilities: [...]` lists and legacy `capability_profile=saas` into
  `capabilities: {business: [saas]}`.
- **Reuse**: YAML loading pattern from `ai/runtime/skill_registry.py`
  (`_load_yaml`); dataclass-based modeling style from
  `ai/runtime/dependency_graph.py` (`Node`/`Edge` as the precedent for typed,
  serializable descriptor objects).
- **Conflict to resolve**: `ai/installer.py` currently hardcodes
  `CAPABILITY_PROFILES = {"saas"}` and `SAAS_ONLY_PATHS`. SPEC-FW-006 itself
  should *not* remove these (that's SPEC-FW-007's job) — it only needs to
  define the registry and descriptors *alongside* the existing hardcoded
  logic, proving the registry can represent at least the `saas` capability
  that `SAAS_ONLY_PATHS` currently encodes by hand.

### SPEC-FW-007 — Installer Registry Integration

- **Missing**: replace `CAPABILITY_PROFILES`/`SAAS_ONLY_PATHS`/
  `should_copy_capability_path` with registry-driven path resolution sourced
  from `ai/capabilities/*/*.yaml` `paths:` entries; installer must still accept
  legacy `.template-profile` inputs and produce output indistinguishable from
  today for hosts that don't opt into the typed block.
- **Reuse**: `ai/installer.py`'s existing predicate composition style
  (`should_copy_specs_path`, `should_copy_requirements_file`,
  `should_copy_capability_path`, all composed in `iter_template_files`/the
  copy loop) — the registry-driven predicate should slot into the same
  composition rather than restructuring the copy loop.
- **Conflict to resolve**: `prompt_capability_profile` currently asks a single
  yes/no SaaS question. SPEC-FW-007 needs to decide how multi-category,
  multi-value capability selection is prompted (or whether it's
  config-file-driven only for the first iteration) — this is the highest
  product-surface change in the program and the main reason this spec is rated
  **High** risk below.

### SPEC-FW-008 — Shared Profile Parser

- **Missing**: `ai/runtime/profile.py` exposing a single
  `load_profile(project_root) -> Profile` (or similar) that reads
  `.template-profile`, normalizes legacy fields (`package_manager`,
  `environment_profile`, `capability_profile`) and the new typed
  `capabilities:` block (once 006 exists) into one object.
- **Reuse**: the two near-identical `profile_from_template_file` functions in
  `scripts/run_uv_sync.py` and `scripts/hooks/sync_dependencies.py` are the
  direct extraction source — same line-parsing loop
  (`key, separator, value = line.partition("=")`), same
  `ENVIRONMENT_PROFILES` set. `resolve_profile` in both files (selected →
  persisted → default `"local"`) should also move into `profile.py`.
- **Conflict to resolve**: `sync_dependencies.py`'s `profile_from_template_file`
  only triggers for `manager == "uv"`; `run_uv_sync.py`'s version has no such
  guard. The shared parser should expose the full profile unconditionally and
  let callers decide what to do with `package_manager`.

### SPEC-FW-009 — Restore Project Command

- **Missing**: `scripts/restore_project.py` implementing the 8-step sequence
  from ADR-FW-001 Phase 4 (read profile → normalize legacy → resolve
  capabilities → sync deps → regenerate skills registry → regenerate `.ai/`
  artifacts → regenerate `llms.txt` → validate consistency).
- **Reuse**: `ai/tools/refresh_context.py::refresh_context` already does
  "regenerate skills registry + context bundle + dependency graph + treemap"
  in one function — restore should call this directly rather than
  reimplementing artifact regeneration. Dependency sync should shell out to
  (or import) `scripts/run_uv_sync.py`'s `run_init`/`run_update`. Profile
  reading uses 008's `ai/runtime/profile.py`. Capability resolution uses 006's
  registry.
- **Conflict to resolve**: `refresh_context` doesn't yet produce `llms.txt`
  (that's 010's job) or validate skill/descriptor consistency (also new). 009
  should be sequenced *after* 010 produces the `llms.txt` generator function it
  can call — or 009 ships first with a TODO/no-op for that one step and a
  follow-up wires it once 010 lands. This plan recommends the latter (see
  Phase 3 vs Phase 4 below) to avoid blocking restore on the scanner pipeline.

### SPEC-FW-010 — Multi-Stack Scanner Pipeline (+ llms.txt)

- **Missing**: a Scanner Layer → Intermediate Representation → Generator Layer
  pipeline (per `docs/prompt/upgrade.md` §6) that is language-agnostic; an
  `llms.txt` generator; `ai/context.yaml` additions for the new artifact and
  any new `treemap_ignore_dirs`/structure entries per language.
- **Reuse**: `ai/runtime/dependency_graph.py`'s `Node`/`Edge` dataclasses are
  already a generic IR (`kind`, `module`, `file_path` fields are not
  Python-specific in shape, only in how they're populated) — SPEC-FW-010
  should generalize `_iter_python_files`/`_module_name`/`build_dependency_graph`
  into a scanner-per-language registration mechanism that all emit `Node`/`Edge`,
  rather than introducing a second IR. `ai/tools/refresh_context.py`'s
  `_artifact_path` + `artifact_paths(config)` pattern is the extension point
  for registering the new `llms.txt` artifact.
- **Conflict to resolve**: none structural — this is the most additive of the
  remaining specs. The main design decision is whether scanner selection reads
  from the SPEC-FW-006 registry's `scanners:` descriptor key from day one
  (preferred, per ADR-FW-001) or from a temporary hardcoded language-detection
  fallback for hosts without typed capabilities (SPEC-FW-005 §9 already
  documents this fallback as acceptable for legacy hosts).

### SPEC-FW-011 — SaaS/Supabase/VPS/Domains Capability Expansion

- **Missing**: new descriptors under `ai/capabilities/databases/supabase.yaml`,
  `ai/capabilities/platform/vps.yaml` (or similar), domain/DNS descriptors;
  new skill content (Supabase Auth/Storage/RLS, VPS Docker/Nginx/SSL/Backup,
  DNS/Cloudflare/SSL/Email) under `ai/skills/saas/` or new subdirectories;
  `ai/domains/saas.md` updates linking the new skills.
- **Reuse**: existing `ai/skills/saas/*.md` files as the content/style template;
  `ai/domains/saas.md` + `ai/domains/index.md` linking pattern (SPEC-FW-001's
  contract); `ai/skills.yaml` registry entries follow the existing
  `path`/`description` shape.
- **Conflict to resolve**: none architectural — this is primarily content plus
  descriptors once 006 exists.

### SPEC-FW-012 / 013 / 014 — AI Agent Ecosystem / Kubernetes & Linux / Golang

- **Missing**: for each — new capability descriptors (`ai`, `infrastructure`,
  `platform`, `languages` categories respectively), new skills/domains content,
  and (per ADR-FW-001) new scanners feeding the SPEC-FW-010 pipeline (no
  scanner today handles Go, Kubernetes manifests, or AI-agent code patterns).
- **Reuse**: same descriptor/skill/domain patterns as 011; scanner additions
  plug into the SPEC-FW-010 scanner registry.
- **Conflict to resolve**: **these three specs do not yet exist as written
  documents** — only their names and category assignments are defined in
  ADR-FW-001's Follow-up Specs list. Each needs its own SPEC-FW-0NN document
  (Context/Contract/Invariants/Out of scope, matching the style of
  SPEC-FW-001..005) authored before implementation begins. This plan sequences
  them last specifically because they are both lowest-priority (stack growth,
  not core architecture) and least-specified.

### ADR-FW-002 — uv-only retirement of pip paths

- **Missing**: a decision on retirement *scope* — full removal of
  `scripts/run_pip_init.py` / `requirements.*.txt` / `package_manager` axis
  vs. marking them legacy-but-present. ADR-FW-002's own text says "Support for
  pip will be considered legacy and will not be expanded" — it does **not**
  mandate removal. This plan treats full removal as **out of scope** for the
  initial program (see §10) and recommends only: (a) stop writing new pip-path
  code in 008/009, (b) document `run_pip_init.py`/`PACKAGE_MANAGERS` as legacy
  in code comments/specs, (c) leave removal as a future, separately-scoped
  cleanup once no active hosts report `package_manager=pip`.
- **Reuse**: n/a (removal-oriented).

---

## 5. Impact Analysis

| Spec | Files affected | Risk level | Breaking-change potential |
|---|---|---|---|
| **SPEC-FW-006** | New: `ai/capabilities/**/*.yaml`, `ai/runtime/capability_registry.py`. No existing files modified. | **Low** | **None** — purely additive; nothing references these files yet. |
| **SPEC-FW-007** | `ai/installer.py` (core rewrite of capability-related constants/functions: `CAPABILITY_PROFILES`, `SAAS_ONLY_PATHS`, `prompt_capability_profile`, `validate_capability_profile`, `should_copy_capability_path`, `iter_template_files` composition, `.template-profile` writer). | **High** | **Low** — if the registry is seeded with descriptors that reproduce today's `saas`-only behavior exactly, and legacy `.template-profile` files keep parsing per ADR-FW-001's compatibility strategy, hosts see no behavior change. Risk is concentrated in *prompting UX changes* for multi-category selection, not in file-copy outcomes. |
| **SPEC-FW-008** | `ai/runtime/profile.py` (new); `scripts/run_uv_sync.py` (replace local `profile_from_template_file`/`resolve_profile` with import); `scripts/hooks/sync_dependencies.py` (same). | **Medium** | **Low** — internal refactor of two call sites; external CLI behavior (`run_uv_sync.py init/update/reset`, `sync_dependencies.py`) unchanged if the shared parser preserves current semantics (including the uv-only guard quirk noted in §4). |
| **SPEC-FW-009** | New: `scripts/restore_project.py`. Possibly small additions to `ai/tools/refresh_context.py` if restore needs a programmatic entrypoint vs. CLI subprocess call. | **Medium** | **None** — new command, nothing depends on it existing. |
| **SPEC-FW-010** | `ai/runtime/dependency_graph.py` (generalize Python-only scanning into a registry of per-language scanners sharing `Node`/`Edge`); new `ai/runtime/llms_txt.py` (or similar); `ai/tools/refresh_context.py` (register new artifact + new scanners); `ai/context.yaml` (new artifact path, possibly new structure/ignore entries). | **Medium** | **None** — `.ai/` artifacts and `llms.txt` are documented as optional/regeneratable (SPEC-FW-005 §9: "`.ai/` never required at runtime"); existing Python-only output remains a subset of the generalized output. |
| **SPEC-FW-011** | New descriptor/skill/domain content only (`ai/capabilities/databases/`, `ai/capabilities/platform/`, `ai/skills/saas/*` additions, `ai/domains/saas.md`, `ai/skills.yaml` entries). Possibly `pyproject.toml` new optional-dependency groups (e.g. `supabase`). | **Low** | **None** — additive content; existing hosts unaffected unless they opt in. |
| **SPEC-FW-012** | New: `ai/capabilities/ai/*.yaml`, skills/domains content, scanner addition in SPEC-FW-010's registry. | **Medium** | **None** — additive, but scanner addition touches shared scanner-registration code from 010. |
| **SPEC-FW-013** | New: `ai/capabilities/infrastructure/kubernetes.yaml`, `ai/capabilities/platform/linux.yaml`, content, scanner addition; possible reorganization of `scripts/linux/` under capability-driven delivery. | **Medium** | **Low** — `scripts/linux/` already exists and is delivered to all hosts; making it capability-conditional could *remove* it from hosts that don't declare `platform: [linux]`, which is a behavior change for existing Linux hosts unless they're auto-detected/defaulted. |
| **SPEC-FW-014** | New: `ai/capabilities/languages/golang.yaml`, content, Go scanner addition in 010's registry. | **Medium** | **None** — additive. |
| **ADR-FW-002 (transversal: pip retirement scope)** | `ai/installer.py` (`PACKAGE_MANAGERS`, `prompt_package_manager`, `validate_package_manager`), `scripts/hooks/sync_dependencies.py` (`PACKAGE_MANAGERS`, `--manager`, pip branches in `dependency_files`/`install_command`), `scripts/run_pip_init.py` (deprecation marker only, per this plan's recommendation). | **Medium** | **Medium** for any host still relying on `package_manager=pip` / `requirements.*.txt` — mitigated by *not* removing these in this program (legacy-marking only, per §4's recommendation). |

---

## 6. Migration Complexity

| Spec | Implementation effort | Testing effort | Migration effort | Notes |
|---|---|---|---|---|
| **SPEC-FW-006** | M | S | None | New directory tree + loader module; testing is mostly schema/parsing unit tests; no migration since nothing consumes it yet. |
| **SPEC-FW-007** | L | L | S | Core installer logic change; testing must cover both legacy `.template-profile` inputs and new typed-block inputs producing identical file sets for equivalent configurations (regression/dry-run diff). Migration is "none" for hosts (legacy files still parse) but "small" for the template's own documentation/prompts. |
| **SPEC-FW-008** | S | S | None | Mechanical extraction of ~15-line function into a shared module; unit tests for normalization edge cases (legacy flat list, legacy `capability_profile=`, new typed block, missing file). |
| **SPEC-FW-009** | M | M | None | New orchestrator script composing existing pieces (`run_uv_sync`, `refresh_context`, registry); testing is mostly idempotency (`restore` run twice produces no diff) and consistency validation. |
| **SPEC-FW-010** | L | L | None | Generalizing the dependency-graph scanner and adding `llms.txt` generation is the largest single engineering effort in the program; testing needs fixtures per language (Python today, at least one non-Python fixture to prove generalization). |
| **SPEC-FW-011** | M | S | None | Mostly content authoring (skills, descriptors); testing is descriptor-schema validation + skill registry consistency (extends SPEC-FW-003 invariant). |
| **SPEC-FW-012** | M | S | None | Content + one new scanner; depends on 010's scanner-registration API existing first. |
| **SPEC-FW-013** | M | M | S | Content + scanner + the `scripts/linux/` delivery-conditionality question (migration effort because existing Linux hosts must keep receiving these scripts — likely via a `platform: [linux]` default/auto-detect). |
| **SPEC-FW-014** | M | S | None | Content + new Go scanner; same shape as 012. |
| **ADR-FW-002 (pip legacy-marking)** | S | S | None (by design) | Comments/doc updates + small conditionals; explicitly not removing pip paths avoids migration cost in this program. |

---

## 7. Phase-by-Phase Implementation Roadmap

### Phase 0 — UV Standardization Cleanup (ADR-FW-002)

- **Goal**: Make ADR-FW-002's "no new pip functionality" decision visible and
  enforced in code without removing existing pip support, so later phases
  (008, 009) don't add *more* pip-aware code.
- **Specs included**: ADR-FW-002 (no SPEC-FW-0NN number; transversal cleanup).
- **Dependencies**: None. Can start immediately.
- **Deliverables**:
  - Code comments/docstrings in `ai/installer.py`, `scripts/run_pip_init.py`,
    and `scripts/hooks/sync_dependencies.py` marking `package_manager="pip"`
    and `run_pip_init.py` as legacy per ADR-FW-002.
  - Confirmation (no code change) that `pyproject.toml` + `uv.lock` remain the
    authoritative dependency source for `uv` hosts.
  - A short addendum note (in this plan or a follow-up ADR, see §10) recording
    the decision: pip paths are marked legacy, not removed, in this program.
- **Validation criteria**: `grep` for `package_manager`/`PACKAGE_MANAGERS`/
  `run_pip_init` shows only legacy-marked occurrences; no new pip call sites
  introduced; existing `make`/`uv sync` workflows unchanged (verified by
  running `scripts/run_uv_sync.py init --dry-run`).

### Phase 1 — Foundations (SPEC-FW-006 + SPEC-FW-008)

- **Goal**: Establish the typed capability registry and the shared profile
  parser as new, additive modules — the two pieces every later phase depends
  on.
- **Specs included**: SPEC-FW-006, SPEC-FW-008.
- **Dependencies**: Phase 0 (so 008 doesn't need to account for new pip code
  paths).
- **Deliverables**:
  - `ai/capabilities/<category>/*.yaml` for at least the categories needed to
    represent today's capabilities (`business/saas.yaml`, `languages/python.yaml`,
    `cloud/aws.yaml`, `infrastructure/terraform.yaml`, `frameworks/react.yaml`)
    using the descriptor schema from ADR-FW-001 (`name`, `type`, `depends_on`,
    `paths`, `dependencies`, `scanners`, `hooks`, `artifacts`).
  - `ai/runtime/capability_registry.py`: loader + normalization (flat list,
    legacy `capability_profile=`, typed block → unified model).
  - `ai/runtime/profile.py`: `load_profile()` extracted from
    `scripts/run_uv_sync.py`/`scripts/hooks/sync_dependencies.py`'s
    `profile_from_template_file`/`resolve_profile`, extended to read
    `package_manager`/`capability_profile`/typed `capabilities:` block.
  - `scripts/run_uv_sync.py` and `scripts/hooks/sync_dependencies.py` updated
    to import from `ai/runtime/profile.py` instead of local copies (mechanical;
    behavior-preserving).
- **Validation criteria**: Unit tests for `capability_registry.py` covering
  all 9 categories' descriptor parsing and legacy normalization; unit tests
  for `profile.py` covering legacy-only `.template-profile`, typed-block
  `.template-profile`, and missing-file cases; `scripts/run_uv_sync.py init
  --dry-run` and `scripts/hooks/sync_dependencies.py` produce identical output
  before/after the extraction (regression check).

### Phase 2 — Installer Refactor (SPEC-FW-007)

- **Goal**: Make `ai/installer.py` resolve capability-driven paths from the
  registry instead of hardcoded `CAPABILITY_PROFILES`/`SAAS_ONLY_PATHS`.
- **Specs included**: SPEC-FW-007.
- **Dependencies**: Phase 1 (registry + descriptors must exist; shared parser
  must exist).
- **Deliverables**:
  - `ai/installer.py` capability-related logic rewritten to call
    `capability_registry` for path resolution, while
    `should_copy_capability_path`'s *call site* in the existing predicate
    composition (`iter_template_files`) is preserved.
  - `.template-profile` writer extended to optionally emit the typed
    `capabilities:` block (additive — legacy fields `package_manager=`/
    `environment_profile=`/`capability_profile=` still written for backward
    compatibility per ADR-FW-001).
  - Installer prompt flow updated for multi-category selection OR explicitly
    deferred to config-file-driven input for v1 (decision recorded in §10).
- **Validation criteria**: Dry-run diff — installing with today's
  `saas`-only flow against the new registry-driven installer produces the
  same file set as before (using `ai/capabilities/business/saas.yaml` seeded
  in Phase 1 to reproduce `SAAS_ONLY_PATHS`); a legacy `.template-profile`
  (no typed block) round-trips through install → restore (once Phase 3 exists)
  without data loss.

### Phase 3 — Dependency & Restore (SPEC-FW-009)

- **Goal**: Provide a single `restore` command that brings a host back to a
  consistent state from its `.template-profile` + capability registry.
- **Specs included**: SPEC-FW-009.
- **Dependencies**: Phase 1 (profile parser, registry) and Phase 2 (installer's
  registry-driven path resolution, so restore and install share logic).
- **Deliverables**:
  - `scripts/restore_project.py` implementing steps 1-6 and 8 of ADR-FW-001
    Phase 4 (read profile, normalize legacy, resolve capabilities, sync deps
    via `run_uv_sync`, regenerate skills registry + `.ai/` artifacts via
    `refresh_context`, validate consistency). Step 7 (`llms.txt`) is stubbed
    or skipped until Phase 4 lands (see Gap Analysis, SPEC-FW-009).
  - Consistency validation: every `ai/skills.yaml` entry maps to a descriptor
    path declared by an active capability (extends SPEC-FW-003's invariant).
- **Validation criteria**: Running `restore_project.py` twice in a row
  produces no further changes (idempotency); running it after a manual edit to
  `.template-profile` (e.g., adding `capability_profile=saas` by hand) produces
  the same result as running the installer with that capability selected.

### Phase 4 — Artifact System / Multi-Stack Scanner Pipeline (SPEC-FW-010)

- **Goal**: Generalize artifact/dependency scanning beyond Python and add
  `llms.txt` generation.
- **Specs included**: SPEC-FW-010.
- **Dependencies**: Phase 1 only (needs descriptor `scanners:`/`artifacts:`
  keys to exist). **Can run in parallel with Phases 2-3** by a separate
  workstream, since it does not touch `ai/installer.py` or
  `scripts/restore_project.py` directly.
- **Deliverables**:
  - `ai/runtime/dependency_graph.py` generalized: scanner registration keyed by
    capability `type` (e.g., `language`), Python scanner becomes one
    registered scanner among others, `Node`/`Edge` IR unchanged.
  - `ai/runtime/llms_txt.py` (or similar) generating `llms.txt` from project
    inspection + capability registry + skills registry, per
    `docs/prompt/upgrade.md` §5 goals (project summary, architecture summary,
    current capabilities, relevant specs, agent onboarding).
  - `ai/tools/refresh_context.py` updated to register the `llms.txt` artifact
    via the existing `_artifact_path`/`artifact_paths` pattern.
  - `ai/context.yaml` updated with the new artifact path and any new
    `structure`/`ignore` entries needed for non-Python scanning.
  - Follow-up wiring of Phase 3's restore step 7 (`llms.txt` regeneration) now
    that the generator exists.
- **Validation criteria**: `refresh_context` regenerates `llms.txt` alongside
  existing artifacts with no errors on the current (Python-only) repo;
  existing `.ai/dependencies_graph.json` output for Python files is unchanged
  (regression fixture comparison) after generalization.

### Phase 5 — Capability Expansion: SaaS/Supabase/VPS/Domains (SPEC-FW-011)

- **Goal**: Flesh out the SaaS-adjacent stack (Supabase, VPS, Domains) as
  typed capabilities with real skill content.
- **Specs included**: SPEC-FW-011.
- **Dependencies**: Phase 1 (descriptors), Phase 2 (so new paths are actually
  delivered to hosts that opt in).
- **Deliverables**:
  - New descriptors: `ai/capabilities/databases/supabase.yaml`,
    `ai/capabilities/platform/vps.yaml` (or equivalent), domain/DNS descriptor.
  - New skill content under `ai/skills/saas/` (or new subdirectories) covering
    Supabase Auth/Storage/RLS, VPS Docker/Nginx/SSL/Backup, DNS/Cloudflare/SSL/
    Email, per `docs/prompt/upgrade.md` §4.
  - `ai/domains/saas.md` and `ai/skills.yaml` updated with new entries.
  - New `pyproject.toml` optional-dependency group(s) if Supabase client
    libraries are needed (e.g., a `supabase` extra).
- **Validation criteria**: Installing with the new capabilities selected
  delivers the new skill files and nothing else changes for hosts that don't
  select them; SPEC-FW-003 consistency invariant holds for the new entries.

### Phase 6 — Stack Growth: AI Agents, Kubernetes/Linux, Golang (SPEC-FW-012/013/014)

- **Goal**: Extend the typed registry and scanner pipeline to three new stack
  areas.
- **Specs included**: SPEC-FW-012, SPEC-FW-013, SPEC-FW-014.
- **Dependencies**: Phase 1 (registry) and Phase 4 (scanner pipeline must be
  generalized before new scanners can be registered).
- **Deliverables**:
  - **Pre-requisite for this phase**: SPEC-FW-012, -013, -014 documents
    themselves must be authored (Context/Contract/Invariants/Out of scope),
    since they currently exist only as names + category assignments in
    ADR-FW-001's Follow-up Specs list.
  - Per spec: new descriptors (`ai/capabilities/ai/*.yaml`,
    `ai/capabilities/infrastructure/kubernetes.yaml`,
    `ai/capabilities/platform/linux.yaml`, `ai/capabilities/languages/golang.yaml`),
    skill/domain content, and a scanner registered with Phase 4's pipeline
    (AI-agent code patterns, Kubernetes manifests, Go).
  - SPEC-FW-013 specifically must resolve the `scripts/linux/` delivery
    question (currently delivered to all hosts; becoming capability-gated
    requires a default/auto-detect so existing Linux hosts don't lose these
    scripts).
- **Validation criteria**: Each new scanner produces valid `Node`/`Edge`
  output on a fixture project for its language/stack; SPEC-FW-003 invariant
  holds; existing hosts without `platform: [linux]` declared either still
  receive `scripts/linux/` (if defaulted) or the removal is called out as an
  explicit, documented breaking change for that subset.

### Phase 7 — Pip Legacy Retirement (SPEC-FW-015)

- **Goal**: Complete ADR-FW-002 by removing the `pip`/`requirements*.txt` code
  paths that Phase 0 marked legacy, leaving `uv` + `pyproject.toml`/`uv.lock`
  as the installer's only supported dependency mechanism.
- **Specs included**: SPEC-FW-015.
- **Dependencies**: Phase 0 (legacy-marking — already done) and Phase 1
  (`ai/runtime/profile.py`/`capability_registry.py` — already implemented, so
  the uv path this spec makes exclusive already exists and is exercised).
  Independent of Phases 2/3/4/5/6.
- **Deliverables**:
  - `ai/installer.py`: remove `PACKAGE_MANAGERS`, `prompt_package_manager`,
    `validate_package_manager`, the `*_REQUIREMENTS_PATH` constants,
    `should_copy_requirements_file`, and the `package_manager` parameter from
    `install_template`/`iter_template_files`/`render_target_file`/
    `copy_template_file`; collapse `should_copy_package_file` to the uv branch
    only.
  - `scripts/hooks/sync_dependencies.py`: remove `PACKAGE_MANAGERS`,
    `--manager`, `requirement_files`, `REQUIREMENTS_GLOB`, and the pip branches
    of `dependency_files`/`install_command`.
  - Delete `scripts/run_pip_init.py`; `Makefile`'s `init` target becomes the
    `uv` variant unconditionally.
  - `install_linux.py`/`install_windows.py`: remove `--package-manager`,
    `--pip`, `--uv` flags and mutual-exclusion validation.
  - `scripts/package.py`: remove `detect_package_manager`,
    `CLOUD_REQUIREMENTS`, `--package-manager`; bundler always uses
    `uv export`.
  - `ai/tools/inspect_project.py`: drop `requirements*.txt` from
    language/cloud detection predicates.
  - `ai/capabilities/business/saas.yaml`: remove the `requirements.saas.txt`
    path entry.
  - Delete `requirements.local.txt`, `requirements.cloud.txt`,
    `requirements.dev.txt`, `requirements.saas.txt` from the template repo.
  - Update `tests/test_installer.py`, `tests/test_script_wrappers.py`,
    `tests/test_sync_dependencies.py`, `tests/test_restore_project.py` to drop
    pip-specific cases/fixtures.
  - Update `README.md`, `docs/linux_setup/README.md`,
    `docs/windows_setup/README.md`; regenerate `docs/treemap.md`.
- **Validation criteria**: `git grep -i "package_manager\|PACKAGE_MANAGERS"`
  returns zero matches under `ai/`, `scripts/`, `install_linux.py`,
  `install_windows.py`; `git ls-files | grep -i requirements` returns zero
  matches; `pytest -q`, `ruff check .`, `ruff format --check .` pass;
  `python scripts/restore_project.py --dry-run --pretty` still reports zero
  `missing` entries. **Breaking change** (documented): hosts with
  `package_manager=pip` in `.template-profile` must follow SPEC-FW-015's
  Migration Strategy before their next restore/sync.

---

## 8. Risk Matrix

### Highest-risk changes

1. **SPEC-FW-007 (Installer Registry Integration)** — rewrites the core
   `ai/installer.py` capability logic that every host install/update goes
   through. Highest risk in the program.
2. **ADR-FW-002 pip retirement scope** (Phase 0) — if scope creeps from
   "legacy-mark" to "remove", existing `package_manager=pip` hosts break. This
   plan constrains Phase 0 to legacy-marking only specifically to keep this
   risk at Medium/contained.

### Most invasive changes

1. **SPEC-FW-007** — touches `ai/installer.py`'s constants, validators,
   prompts, path predicates, and `.template-profile` writer simultaneously.
2. **SPEC-FW-010** — generalizing `ai/runtime/dependency_graph.py` from a
   Python-specific module to a multi-language scanner registry is the largest
   structural change to a runtime module in the program.

### Recommended validation checkpoints

- **After Phase 1**: registry + parser unit tests green; `run_uv_sync.py`/
  `sync_dependencies.py` dry-run output unchanged (regression diff against
  pre-Phase-1 output).
- **After Phase 2**: installer dry-run diff against Phase-1 baseline for (a) a
  legacy `.template-profile` and (b) a fresh install with `saas` selected —
  both must match pre-refactor file sets exactly.
- **After Phase 3**: `restore_project.py` idempotency check (run twice, diff
  is empty); restore-from-legacy-profile matches fresh-install-with-same-options.
- **After Phase 4**: `refresh_context` output diff for `.ai/dependencies_graph.json`
  on the current repo is empty (Python scanning unchanged); `llms.txt`
  generated without error.
- **After Phase 5/6**: SPEC-FW-003 consistency invariant (every `ai/skills.yaml`
  entry resolves to an existing file and an active-or-available descriptor)
  holds across the full registry.

### Recommended rollback strategy

- Each phase lands as its own commit/PR, independently revertible.
- Phases 1 and 4 are purely additive (new files only) — reverting them is a
  pure deletion with zero impact on running hosts, since `.ai/` artifacts and
  `llms.txt` are documented as "never required at runtime" (SPEC-FW-005 §9).
- Phase 0 and Phase 2/3 are the only phases that touch files hosts actively
  depend on (`ai/installer.py`, `.template-profile`, sync scripts). For these:
  - Phase 0's changes are comments/markers only — trivially revertible.
  - Phase 2's installer changes must preserve the legacy `.template-profile`
    parse path per ADR-FW-001's Compatibility Strategy at all times during
    rollout, so a revert of Phase 2 leaves legacy hosts unaffected (they were
    never depending on the new typed block).
  - Phase 3 (`restore_project.py`) is a new, optional command — reverting it
    removes the command but does not affect install/update flows.

---

## 9. Validation Strategy

- **Installer (Phase 2)**: dry-run diff. Run the current installer and the
  refactored installer against the same target directory + `.template-profile`
  combinations (no profile / `local` / `cloud` / `cloud+saas`); diff the
  resulting file trees — must be empty for equivalent inputs.
- **Dependency resolution (Phases 1, 5, 6)**: `uv sync` must resolve the
  correct `--extra`/`--group` set derived from the active typed `capabilities:`
  block (e.g., `business: [saas]` → existing `local`/`cloud` extras plus any
  new `supabase` extra from Phase 5), verified via
  `scripts/run_uv_sync.py init --dry-run` output inspection.
- **Artifact regeneration (Phase 4)**: `refresh_context` must regenerate
  `.ai/context_bundle.yaml`, `.ai/skills_registry.json`,
  `.ai/dependencies_graph.json`, `.ai/treemap.md`, and the new `llms.txt`
  with no errors; Python-only output must be byte-equivalent to pre-Phase-4
  output (proves generalization didn't change existing behavior).
- **Restore idempotency (Phase 3)**: `python scripts/restore_project.py` run
  twice consecutively produces no filesystem changes on the second run.
- **Consistency invariant (extends SPEC-FW-003, all phases adding skills)**:
  every entry in `ai/skills.yaml` has (a) a `path` that exists, and (b) once
  Phase 1 lands, a corresponding descriptor in `ai/capabilities/**` whose
  `paths:` list includes that skill — or is explicitly core (always-delivered,
  no descriptor needed, matching today's AWS/Terraform/Python/Frontend/Data
  Product domains per SPEC-FW-004's "Out of scope").
- **Existing test/lint infrastructure**: `scripts/testing/run_pytest.py`,
  `scripts/testing/run_ruff_check.py`, `scripts/testing/run_ruff_format.py`
  (and the `make test`/`make lint` targets that wrap them) should gain test
  modules for `ai/runtime/capability_registry.py`, `ai/runtime/profile.py`,
  and `scripts/restore_project.py` as each is implemented — no new test
  framework needed.

---

## 10. Recommended Execution Order

```text
Phase 0 (ADR-FW-002 cleanup)
   ↓
Phase 1 (SPEC-FW-006 + SPEC-FW-008)
   ↓                              ↘
Phase 2 (SPEC-FW-007)         Phase 4 (SPEC-FW-010)  ← can run in parallel with Phase 2/3
   ↓                              ↓
Phase 3 (SPEC-FW-009)  ←──────────┘ (restore's llms.txt step wired once Phase 4 lands)
   ↓
Phase 5 (SPEC-FW-011)
   ↓
Phase 6 (SPEC-FW-012, SPEC-FW-013, SPEC-FW-014 — specs to be authored first)

Phase 7 (SPEC-FW-015 — Pip Legacy Retirement)
   ↑ depends only on Phase 0 + Phase 1 (already implemented);
     independent of Phases 2/3/4/5/6, can run any time after Phase 1
```

### Recommended First Spec To Implement

**SPEC-FW-006 — Typed Capability Registry.**

It is the root of the dependency graph, it is purely additive (Risk: Low,
Breaking: None), and it directly unblocks SPEC-FW-008, SPEC-FW-007,
SPEC-FW-009, SPEC-FW-010, and SPEC-FW-011. No other spec in the program can be
meaningfully started — let alone finished — without the descriptor model and
registry it defines.

### Recommended Last Spec To Implement

**SPEC-FW-014 — Golang Capability and Scanner.**

It depends on both SPEC-FW-006 (registry) and SPEC-FW-010 (scanner pipeline),
has no dependents of its own, and represents pure stack-growth (new language
support) rather than core architecture. Among SPEC-FW-012/013/014 — which are
mutually independent and individually orderable — Golang is recommended last
because, unlike SPEC-FW-013 (which must resolve the `scripts/linux/` delivery
question affecting *existing* hosts), it carries no migration risk for hosts
that don't opt in, making it the safest spec to leave for whenever capacity
allows.

---

## Open Decisions / Follow-up ADRs

These are decisions this plan surfaces but does not resolve — they should be
recorded as ADR addenda or short decision notes before the relevant phase
begins:

1. **`llms.txt` commit policy** (already flagged as non-blocking in
   SPEC-FW-005's "Resolved ADRs" section) — must be settled before Phase 4
   completes.
2. **ADR-FW-002 pip retirement scope for Phase 0** — Phase 0 implemented
   "legacy-mark, do not remove". Full removal of
   `scripts/run_pip_init.py`/`requirements.*.txt`/the `package_manager` axis is
   now specified as **SPEC-FW-015 (Phase 7)** — see
   [SPEC-FW-015.md](SPEC-FW-015.md) for the contract, breaking-change scope,
   and migration strategy.
3. **Installer prompt UX for multi-category capability selection (Phase 2)** —
   whether SPEC-FW-007 extends the interactive prompt flow or moves to
   config-file-driven capability selection for v1.
4. **`scripts/linux/` delivery conditionality (Phase 6, SPEC-FW-013)** —
   whether existing hosts get `platform: [linux]` by default/auto-detected, or
   whether this is an explicit documented breaking change for that subset.
5. **Whether SPEC-FW-012/013/014 need their own ADRs** — given they introduce
   new scanners (a new architectural surface area touched by SPEC-FW-010),
   versus being purely descriptor/content additions like SPEC-FW-011.

---

## Out of Scope

- Implementing any code, descriptor, or script described above — this document
  is planning only, per `docs/prompt/implement.md`'s constraints.
- Authoring SPEC-FW-012, SPEC-FW-013, or SPEC-FW-014 themselves — this plan
  sequences them but does not write their Context/Contract/Invariants sections.
- Modifying `ai/installer.py`, `pyproject.toml`, `.template-profile`, or any
  `scripts/*` file.
- Resolving the Open Decisions listed in §10 — they are flagged for follow-up
  ADRs/decision notes, not decided here.
- Full removal of `pip`-related code paths (`scripts/run_pip_init.py`,
  `requirements.*.txt`, the `package_manager` axis) — now specified as
  SPEC-FW-015 (Phase 7), not implemented by this document.

---

## References

- `docs/prompt/implement.md` — source brief for this document.
- `docs/prompt/upgrade.md` — original refactor/upgrade initiative brief
  (capability architecture, dependency management, restore, SaaS expansion,
  llms.txt, multi-stack hooks).
- `specs/rework/SPEC-FW-001.md` through `specs/rework/SPEC-FW-005.md` — current
  state baseline (domains, SaaS skills, descriptor contract, capability
  profiles, planning spec).
- `specs/rework/ADR-FW-001.md` — Typed Capability Registry decision; defines
  SPEC-FW-006..014 and the 6-phase migration plan this roadmap is derived from.
- `specs/rework/ADR-FW-002.md` — UV-only standardization decision.
- `specs/rework/SPEC-FW-015.md` — Pip Legacy Retirement (Phase 7), the
  follow-up spec completing ADR-FW-002.
- `ai/installer.py` — capability profile / environment profile / package
  manager logic (Phase 2 target).
- `ai/runtime/dependency_graph.py`, `ai/runtime/context_bundle.py`,
  `ai/runtime/skill_registry.py` — existing runtime modules whose patterns are
  reused by SPEC-FW-006/008/010.
- `ai/tools/refresh_context.py` — artifact regeneration entrypoint (Phase 3/4
  integration point).
- `scripts/run_uv_sync.py`, `scripts/run_pip_init.py`,
  `scripts/hooks/sync_dependencies.py` — dependency sync scripts (Phase 0/1
  targets).
- `pyproject.toml`, `.template-profile`, `ai/context.yaml`, `ai/skills.yaml`,
  `ai/policies/global.md` — configuration and policy files referenced
  throughout.
