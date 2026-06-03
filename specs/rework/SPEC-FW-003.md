# SPEC-FW-003 — Domain Descriptors for Existing Domains

## Context

SPEC-FW-001 introduced `ai/domains/` as the navigation layer for the framework.
The first implementation created `ai/domains/index.md` (full map) and
`ai/domains/saas.md` (SaaS domain descriptor, the only new domain at that point).

Existing domains — Data Product, AWS, Terraform, Python, Frontend — have no
individual descriptor files. All their context lives only in `ai/domains/index.md`
as a table row. As these domains grow, or when a host project needs to understand
the scope and boundaries of a specific domain, a dedicated descriptor is more
useful than a single large index.

This spec defines the contract for creating those descriptor files.

---

## Contract

One `.md` file per domain under `ai/domains/`:

| Domain | File |
|---|---|
| Data Product | `ai/domains/data-product.md` |
| AWS | `ai/domains/aws.md` |
| Terraform | `ai/domains/terraform.md` |
| Python | `ai/domains/python.md` |
| Frontend (AWS-integrated) | `ai/domains/frontend.md` |

Each file must contain the following sections, in order:

### 1. Purpose
One paragraph. What this domain covers and why it exists as a separate domain.

### 2. Scope
A two-column table: **In scope** / **Out of scope**. Out-of-scope items should
point to the domain that owns them instead.

### 3. Skills
Table of all skills in the domain: skill name, file path, one-line description.
Must stay in sync with `ai/skills.yaml` — if a skill is added to the yaml, it
must be added here too.

### 4. Policies
List of domain-specific policies (if any). Reference `ai/policies/global.md`
for cross-domain policies rather than repeating them.

### 5. References
Links to related domains, specs, and `ai/skills.yaml`.

---

## Invariants

- Every skill registered in `ai/skills.yaml` must appear in exactly one domain descriptor.
- Domain descriptors do not duplicate content from skill files — they reference them.
- `ai/domains/index.md` remains the single-page overview; descriptors are the per-domain detail.
- Descriptors do not contain recipes or implementation patterns — those belong in skill files.

---

## Out of scope

- Creating new skills (covered by SPEC-FW-001 and SPEC-FW-002).
- Modifying existing skill files.
- Reorganizing `ai/skills/` folder structure.
- Adding new domains (each new domain follows the process in `ai/domains/index.md`).

---

## References

- `specs/rework/SPEC-FW-001.md` — domain-based framework refactoring
- `specs/rework/SPEC-FW-002.md` — SaaS domain (the reference implementation of a descriptor)
- `ai/domains/index.md` — master domain index
- `ai/domains/saas.md` — reference descriptor to use as template
- `ai/skills.yaml` — authoritative skill registry
- `ai/policies/global.md` — global policies referenced by all descriptors
