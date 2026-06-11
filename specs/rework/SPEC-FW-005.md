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
planning document — it does not implement code.** Where `upgrade.md` asks to
"evaluate" a design (notably the capability system), this spec presents options
with trade-offs and records the choice as a pending ADR rather than deciding for
the maintainer.

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
| Two overlapping selection axes | `environment_profile` (local/cloud) + `capability_profile` (saas only) + `package_manager` | A project that evolves `local → cloud → saas` must re-run the installer with `--force` and re-answer three prompts; there is no single source of truth for "what does this host have." |
| Dependency sync is reactive only | `scripts/hooks/sync_dependencies.py` (`dependencies_hash`, `HASH_FILE`) | Detects manifest *changes* and re-installs, but cannot *regenerate* `requirements.*.txt` / `pyproject` extras when a capability is added or removed. |
| No restore entrypoint | — | `upgrade.md` §3 requires `framework restore` / `scripts/restore_project.py`; nothing currently re-derives skills/hooks/artifacts from the capability set after drift (e.g. manual edits to `ai/skills.yaml`, stale `.ai/`). |
| Dependency graph scanner is Python-specific | `ai/runtime/dependency_graph.py`: `_iter_python_files`, `_module_name`, `ast.parse` | The IR (`Node`/`Edge`) is already language-neutral, but `build_dependency_graph` couples scanning + IR construction in one Python-only function. Cannot add a TS/React scanner without duplicating the function. |
| `refresh_context.py` artifact set is fixed | `ai/tools/refresh_context.py`: hardcoded calls to 4 builders, `_artifact_path` requires all 4 filenames in `ai/context.yaml.artifacts` | Adding `llms.txt` (or skipping artifacts for capabilities that don't need them) requires editing this function directly; no plug-in/registration model. |
| SaaS domain has 3 of ~12 needed sub-areas | `ai/skills/saas/` (frontend, backend, database, auth, analytics, deployment, ux — 7 files) | `upgrade.md` §4 asks for Supabase (Storage, RLS detail), VPS (Docker/Nginx/SSL/Backup), Domains (DNS/Cloudflare/SSL/Email) — none exist as skills yet. |
| `.template-profile` schema is fixed at 3 lines | `ai/installer.py` `render_target_file` (TEMPLATE_PROFILE_PATH branch); read by `scripts/run_uv_sync.py::profile_from_template_file` and `scripts/hooks/sync_dependencies.py::profile_from_template_file` (duplicated logic in both files) | A capability list needs a 4th line/format, and the parsing logic is already duplicated across two scripts — a third consumer (restore) would triplicate it. |

---

## 3. Proposed Architecture

```
                    ┌─────────────────────────┐
                    │   Capability Registry    │
                    │  ai/capabilities/*.yaml  │
                    │  (paths, deps, skills,   │
                    │   domains per capability)│
                    └────────────┬─────────────┘
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

- The capability registry is the **single source of truth** consumed by the
  installer (what to copy), restore (what to sync/regenerate), and the artifact
  pipeline (what to scan/generate).
- The Scanner → IR → Generator split isolates language-specific code (scanners)
  from artifact logic (generators), reusing the existing `Node`/`Edge` dataclasses
  as the IR — no new data model needed.
- `restore` is an **orchestrator over existing scripts**, not a new execution
  engine — it calls `run_uv_sync.py`, `build_and_persist_skills_registry`,
  `refresh_context.refresh_context`, etc., in sequence.

---

## 4. Migration Strategy

Incremental, one subsystem per follow-up spec (`SPEC-FW-006`+), so each lands as
an independently reviewable change:

1. **SPEC-FW-006 — Capability registry** (foundation for everything else).
   Introduce `ai/capabilities/*.yaml` descriptors and a loader in
   `ai/runtime/`. Migrate the existing `saas` capability from
   `SAAS_ONLY_PATHS` to a descriptor. No behavior change for hosts.
2. **SPEC-FW-007 — Installer generalization.**
   Replace `CAPABILITY_PROFILES`/`SAAS_ONLY_PATHS`/`should_copy_capability_path`
   with registry-driven logic supporting a list of capabilities. Extend
   `.template-profile` format (see Backward Compatibility below).
3. **SPEC-FW-008 — Dependency manifest regeneration.**
   Add capability → dependency mapping (reusing `pyproject.toml` extras/groups
   as the manifest format) and a regeneration command that rewrites
   `requirements.*.txt` for `pip` hosts from the active capability set.
4. **SPEC-FW-009 — Restore subsystem.**
   `scripts/restore_project.py`, orchestrating sync + skills regen + artifact
   refresh + consistency validation, gated behind the registry from
   SPEC-FW-006/007.
5. **SPEC-FW-010 — Scanner/IR/Generator pipeline + llms.txt.**
   Extract `_iter_python_files`/`ast` scanning from `dependency_graph.py` into
   a `python_scanner`, add a minimal `ts_scanner` (package.json + import regex),
   and add an `llms.txt` generator consuming `context_bundle` + `skills_registry`
   + active capabilities.
6. **SPEC-FW-011 — SaaS capability expansion.**
   New skills for Supabase Storage/RLS, VPS (Docker/Nginx/SSL/Backup), and
   Domains (DNS/Cloudflare/SSL/Email), each as its own capability descriptor
   per SPEC-FW-006.

Each spec should land independently; none requires the others to be useful
(SPEC-FW-006 is the only hard prerequisite for 007–009).

---

## 5. Backward Compatibility Strategy

- **`.template-profile`** — keep `package_manager=` and `environment_profile=`
  lines exactly as-is (read by `scripts/run_uv_sync.py` and
  `scripts/hooks/sync_dependencies.py`). Add a new `capabilities=` line
  (comma-separated) that supersedes `capability_profile=` (currently a single
  optional value written by SPEC-FW-004). Both readers already tolerate unknown
  lines (they iterate and match by key), so old `.template-profile` files
  without `capabilities=` remain valid — treated as `capabilities=` (empty).
- **Existing hosts with `capability_profile=saas`** — the registry loader treats
  `capability_profile=saas` as equivalent to `capabilities=saas` if the new key
  is absent, so no forced re-install.
- **`.ai/` artifacts** — remain optional and regenerable (per `ai/context.yaml`
  rule: ".ai/ is optional generated context and is never required at runtime").
  `llms.txt` follows the same rule: regenerable, not required.
- **`environment_profile` (local/cloud)** stays as-is regardless of which
  capability-system option (A or B, see §7) is eventually chosen — Option A keeps
  it unchanged; Option B's migration path is described in §7 itself.

---

## 6. Folder Structure Proposal

Additions only — no existing paths move:

```
ai/
├── capabilities/                # NEW — capability descriptors (SPEC-FW-006)
│   ├── python.yaml
│   ├── aws.yaml
│   ├── terraform.yaml
│   ├── saas.yaml
│   ├── supabase.yaml            # NEW capability (SPEC-FW-011)
│   ├── vps.yaml                 # NEW capability (SPEC-FW-011)
│   └── domains.yaml              # NEW capability (SPEC-FW-011)
├── runtime/
│   ├── capability_registry.py   # NEW — loads ai/capabilities/*.yaml (SPEC-FW-006)
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

## 7. Capability System Design (two options — pending ADR)

`upgrade.md` explicitly asks to "evaluate replacing profiles with a
capability-based architecture." Two viable paths exist; **this spec does not
choose between them** — the choice is recorded as a **pending ADR** (see
"Pending ADRs" below) for the maintainer to resolve before SPEC-FW-007 begins.

### Option A — Capabilities additive to existing profiles (compatible evolution)

Keep `environment_profile` (local/cloud) and `package_manager` exactly as they
are today. Generalize the existing single-value `capability_profile` (only
`saas` today, per SPEC-FW-004) into a list: `capabilities: [python, aws,
terraform, saas, supabase]`.

- `.template-profile` gains one new line: `capabilities=saas,supabase` (comma
  separated), alongside the unchanged `package_manager=` / `environment_profile=`.
- `SAAS_ONLY_PATHS` becomes a registry lookup: for each capability in the list,
  union its `paths` from `ai/capabilities/<name>.yaml`.
- `should_copy_capability_path` becomes a single function that checks membership
  against the union of active capability paths instead of one hardcoded set.
- `local`/`cloud` continue to gate `specs/` (cloud-only) and the optional
  `src/`/`infra/`/`tests/` structure, unchanged.

| Impact area | Change required |
|---|---|
| `ai/installer.py` | Generalize `CAPABILITY_PROFILES`/`SAAS_ONLY_PATHS` to registry-driven; `prompt_capability_profile` becomes a multi-select prompt or repeated y/N per capability. |
| `.template-profile` | Add one line; existing two lines untouched. |
| `scripts/run_uv_sync.py`, `scripts/hooks/sync_dependencies.py` | No change to `environment_profile` reading; optionally read `capabilities=` for future dependency regeneration (SPEC-FW-008). |
| Existing hosts | Fully compatible — `capability_profile=saas` still parses; new hosts get `capabilities=`. |

**Trade-off:** three overlapping concepts remain (`environment_profile`,
`package_manager`, `capabilities`) — `local`/`cloud` are themselves arguably
capabilities (e.g. `aws`, `terraform`) but are kept as a separate axis. Lower
risk, smaller diff, ships incrementally.

### Option B — Pure capability list (replacement)

Single axis: `capabilities: [python, fastapi, react, postgres, aws, terraform,
supabase, saas]`, matching the `upgrade.md` example exactly. `local` and `cloud`
become either capabilities themselves (`aws` implies cloud-ish behavior) or are
dropped in favor of finer-grained capabilities (`aws`, `terraform` present ⇒
"cloud"; absent ⇒ "local").

| Impact area | Change required |
|---|---|
| `ai/installer.py` | `prompt_environment_profile`, `validate_environment_profile`, `should_copy_specs_path` (which gates `specs/` on `environment_profile == "cloud"`) all need to be re-derived from capability membership (e.g. `specs/` copied iff `"aws"` or `"terraform"` in capabilities). |
| `.template-profile` | Schema change: `environment_profile=` line removed or kept only as a derived/legacy mirror. |
| `scripts/run_uv_sync.py::profile_from_template_file`, `scripts/hooks/sync_dependencies.py::profile_from_template_file` | Both currently parse `environment_profile=cloud\|local` to decide `--extra cloud` / `--group dev-cloud`. Must be rewritten to derive the equivalent from `capabilities=`. **This logic is duplicated in both files today** — Option B is a good forcing function to extract it into one shared helper (e.g. `ai/runtime/profile.py`), but that extraction is in-scope only if Option B is chosen. |
| Existing hosts | **Breaking** — old `.template-profile` files have no `capabilities=` line. Requires a migration shim: on first `restore` run, derive `capabilities=` from the legacy `environment_profile=`/`capability_profile=` pair (e.g. `cloud` → `[aws, terraform]`, `local` → `[]`, `capability_profile=saas` → append `saas`). |

**Trade-off:** matches `upgrade.md`'s example more literally and removes the
overlapping-axes problem permanently, but is a breaking change requiring a
migration shim and touches more files (`run_uv_sync.py`,
`sync_dependencies.py`, `should_copy_specs_path`, all profile prompts).

### Common ground (applies regardless of A or B)

- Both options need the **capability registry** (`ai/capabilities/*.yaml`,
  SPEC-FW-006) — build this first either way.
- Both options replace `SAAS_ONLY_PATHS` with registry-driven path resolution.
- Both options support adding `supabase`, `vps`, `domains` as new capability
  descriptors without installer code changes (SPEC-FW-011).

---

## 8. Dependency Management Design

**Manifest format:** reuse `pyproject.toml` `[project.optional-dependencies]`
(extras) and `[dependency-groups]` (dev groups) as the canonical manifest —
already categorized (`local`, `cloud`, `saas` extras; `dev-local`, `dev-cloud`
groups). Each new capability gets its own extra (e.g. `supabase`, `vps` if it
ever needs Python deps) following the existing pattern.

**Capability → dependency mapping:** each `ai/capabilities/<name>.yaml`
descriptor (SPEC-FW-006) declares a `dependencies:` key naming the
`pyproject.toml` extra(s)/group(s) it requires:

```yaml
# ai/capabilities/saas.yaml
name: saas
paths:
  - ai/skills/saas
  - ai/domains/saas.md
dependencies:
  extras: [saas]
  groups: []
skills_domain: saas
```

**Regeneration workflow (SPEC-FW-008):**

- For `uv` hosts: no regeneration needed — `uv sync --extra <name>` per active
  capability already works via `scripts/run_uv_sync.py::sync_command`, which
  just needs to iterate active capabilities' `dependencies.extras` instead of
  the hardcoded `if profile == "cloud"` branch.
- For `pip` hosts: add a `regenerate-requirements` step that, for each active
  capability, appends its extra's dependency list (read from `pyproject.toml`
  via `tomllib`) into the corresponding `requirements.<capability-or-profile>.txt`.
  This keeps `requirements.*.txt` as a generated projection of `pyproject.toml`
  for pip hosts, while `pyproject.toml` remains the single manifest.
- **Restoration**: if `requirements.*.txt` or `pyproject.toml` is deleted/corrupted,
  `restore` regenerates pip requirement files from `pyproject.toml` + active
  capabilities, and re-runs `uv sync`/`pip install` via the existing
  `sync_dependencies.py` (just re-triggered, no new install logic needed).

**Hash-based skip** (`dependencies_hash` in `sync_dependencies.py`) is retained
unchanged — regeneration runs *before* the hash check, so a no-op regeneration
still short-circuits via the existing hash comparison.

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
  all scanners whose file types are present (detected via
  `ai/tools/inspect_project.py::_detect_languages`, which already detects
  python/sql/terraform — extend with `typescript`/`javascript`).
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
| Current capabilities | `.template-profile` (`capabilities=` line, post SPEC-FW-006/007) |
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

| Spec | Scope | Depends on | Est. size |
|---|---|---|---|
| SPEC-FW-006 | Capability registry (`ai/capabilities/*.yaml` + loader) | — | Small |
| SPEC-FW-007 | Installer generalization (registry-driven paths, multi-capability prompt) | SPEC-FW-006 + **ADR: Option A vs B** | Medium |
| SPEC-FW-008 | Dependency manifest regeneration (pip requirements from pyproject extras) | SPEC-FW-006 | Medium |
| SPEC-FW-009 | Restore subsystem (`scripts/restore_project.py`) | SPEC-FW-006, 007, 008 | Medium |
| SPEC-FW-010 | Scanner/IR/Generator split + `llms.txt` | — (independent of capability work) | Medium |
| SPEC-FW-011 | SaaS expansion: Supabase Storage/RLS, VPS, Domains skills + capabilities | SPEC-FW-006 | Large (mostly content) |

**Suggested order:** SPEC-FW-006 first (unblocks 007/008/009/011). SPEC-FW-010
(`llms.txt` + scanner split) can proceed in parallel — it has no dependency on
the capability work. SPEC-FW-007 requires the pending ADR (Option A vs B)
resolved before starting.

---

## 12. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Option B (pure capabilities) breaks existing host `.template-profile` files | Medium (only if Option B chosen) | High — hosts fail to sync deps | Migration shim in `restore` derives `capabilities=` from legacy `environment_profile`/`capability_profile` on first run (described in §7 Option B). |
| Capability registry YAML drifts out of sync with `ai/skills.yaml` / `ai/domains/` | Medium | Medium — agent gets inconsistent guidance | Add a `restore` validation step (SPEC-FW-009) that checks every skill in `ai/skills.yaml` maps to exactly one capability descriptor, extending the existing SPEC-FW-003 invariant ("every skill appears in exactly one domain descriptor"). |
| TS/React scanner (SPEC-FW-010) produces noisy/incorrect edges with regex-based parsing | Medium | Low — affects only `dependencies_graph.json`, which is optional `.ai/` context | Keep scope minimal (package.json + top-level imports); document known limitations; do not block on full AST accuracy since `.ai/` is "never required at runtime". |
| `llms.txt` at repo root becomes another artifact to keep in sync, adding maintenance burden | Low | Low | Generate purely from existing artifacts (no new scanning); regenerated automatically by `ai-refresh` pre-commit hook, same as other `.ai/` artifacts. |
| SaaS expansion (SPEC-FW-011) grows `ai/skills/saas/` significantly, increasing agent context size for non-SaaS hosts | Low | Medium | Already mitigated by the capability filter (`should_copy_capability_path`) — non-`saas` hosts never receive these files, regardless of Option A/B. |
| Duplicated `.template-profile` parsing logic (`run_uv_sync.py` and `sync_dependencies.py`) diverges further as capabilities are added | Medium | Medium | Extract shared parsing into `ai/runtime/profile.py` as part of SPEC-FW-007, regardless of Option A/B (both need to read the new `capabilities=` line from somewhere). |

---

## Pending ADRs

This spec deliberately leaves the following decisions open. They must be
recorded under `docs/adr/` (per Global Policy 002 — ADR Before Architecture
Change) before the corresponding follow-up spec begins:

1. **Capability system: Option A (additive) vs. Option B (pure replacement)**
   — see §7. Blocks SPEC-FW-007.
2. **`llms.txt` commit policy** — tracked in git vs. gitignored generated
   artifact. See §10. Does not block SPEC-FW-010 (default to gitignored,
   matching `.ai/` precedent, until decided).

---

## Out of scope

- Implementing any of `ai/capabilities/`, `scripts/restore_project.py`,
  `ai/runtime/llms_txt.py`, or scanner modules — these are follow-up specs
  (SPEC-FW-006..011).
- Choosing between capability system Option A and B — recorded as a pending ADR.
- Modifying `ai/installer.py`, `pyproject.toml`, `.pre-commit-config.yaml`, or
  any `ai/skills/` content.
- Future SaaS capabilities explicitly deferred by `SPEC-FW-002`
  ("Future SaaS Capabilities": multi-tenant, billing, payments, notifications,
  WhatsApp, CRM, customer portal) — unaffected by this spec.

---

## References

- `docs/prompt/upgrade.md` — source brief for this spec.
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
- `ai/policies/global.md` — Policy 002 (ADR Before Architecture Change), applicable to the pending ADRs above.
