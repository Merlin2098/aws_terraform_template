# SPEC-FW-004 — Capability Profiles in the Installer

> **Partially superseded.** `ADR-FW-001` (Typed Capability Registry) supersedes
> the single-value `capability_profile` model described here, replacing it with a
> registry-driven, category-typed capability system. `ADR-FW-002` (Standardize on
> UV) supersedes the `package_manager` (`pip` | `uv`) dimension referenced below:
> `uv` is now the sole supported manager and `pip` is legacy. This spec documents
> the installer state *prior* to those ADRs; read it as historical context, with
> the ADRs as the binding direction.

## Context

The installer (`ai/installer.py`) currently supports two orthogonal dimensions:
`environment_profile` (`local` | `cloud`) and `package_manager` (`pip` | `uv`).

With the introduction of the SaaS domain (SPEC-FW-002), a third dimension is
needed: `capability_profile`. Some AI guidance domains are project-type-specific
and should not be delivered to every host. A pure ETL host receiving FastAPI and
Supabase skills gains nothing and adds noise to the agent's context.

Capability profiles are orthogonal to environment profiles. A project can be
`cloud + saas` (e.g. Kadishas), `cloud` only (e.g. a data pipeline), or `local`
(no AWS). The absence of a capability profile is the default (no optional domains).

---

## Contract

### Capability profile values

| Value | Meaning |
|---|---|
| *(none / empty)* | No optional capability domains. Default for all hosts. |
| `saas` | Include the SaaS domain: `ai/skills/saas/` and `ai/domains/saas.md`. |

### Paths controlled by the `saas` capability profile

| Path | Included when |
|---|---|
| `ai/skills/saas/` (entire directory) | `capability_profile == "saas"` |
| `ai/domains/saas.md` | `capability_profile == "saas"` |

All other paths in `ai/` are unaffected by `capability_profile`.

### `.template-profile` record

The `.template-profile` file written to the host must record all three dimensions
so the host can re-install with the same settings:

```
package_manager=uv
environment_profile=cloud
capability_profile=saas
```

When no capability profile is selected, the line is written as:

```
capability_profile=
```

### Installer prompt

The installer asks:

```
Enable SaaS capability domain (FastAPI, Supabase, Railway)? [y/N]:
```

Default is `N` (no capability profile). Answering `y` sets `capability_profile=saas`.

---

## Invariants

- `capability_profile` is independent of `environment_profile`. A `local` host
  can have `saas`; a `cloud` host can have no capability profile.
- The `ai/domains/index.md` file is always copied (it is part of the core guidance
  layer). The SaaS entry inside it may link to a file that does not exist on
  hosts without the SaaS profile — this is acceptable; the agent will not find
  the file and will skip the domain.
- Adding a new capability profile in the future (e.g. `mobile`, `ml`) follows
  the same pattern: add to `CAPABILITY_PROFILES`, define its paths in a constant,
  add a prompt, and wire the filter.

---

## Out of scope

- Capability profiles for existing domains (Data Product, AWS, Terraform, Python,
  Frontend). These are core and always delivered.
- Dynamic generation of `ai/domains/index.md` per profile.
- Removing the SaaS domain from an already-installed host without re-running the
  installer with `--force`.

---

## References

- `ai/installer.py` — implementation
- `specs/rework/ADR-FW-001.md` — typed capability registry (supersedes the single-value `capability_profile` model)
- `specs/rework/ADR-FW-002.md` — UV standardization (supersedes the `pip`/`uv` `package_manager` dimension)
- `specs/rework/SPEC-FW-002.md` — SaaS domain definition
- `specs/rework/SPEC-FW-003.md` — domain descriptor contract
- `specs/template/001-template-contract.md` — overall template contract
