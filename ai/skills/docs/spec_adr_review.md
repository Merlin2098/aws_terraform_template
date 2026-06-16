# Spec and ADR Review

## When to use

- Reviewing or authoring a spec under `specs/project/`
- Reviewing or authoring an ADR under `docs/adr/`
- Checking whether a spec or ADR is complete enough to act on

## Spec review

Specs in this repo use the structure defined in `specs/template/000-template-spec-format.md`:
**Context / Contract / Invariants / Out of scope / References / Avoid**.

When reviewing a spec, consider:

- **Context** — does it explain *why* the spec exists, not just what it describes?
- **Contract** — are the guarantees declarative and concrete? Vague bullets ("handle errors") are not a contract
- **Invariants** — are the things that must stay true across changes actually listed?
- **Out of scope** — does it name what it deliberately skips, to prevent scope creep?
- **References** — do the file paths and linked skills/specs actually exist in the repo?
- **Duplication** — flag if the spec restates principles already in `ai/skills/` or `ai/policies/global.md`; point to the canonical source instead

**Boundary:** `specs/template/` contains inherited contracts and is read-only in host repos — note observations but do not propose edits to those files. `specs/project/` is editable.

## ADR review

ADRs record architectural decisions. Standard format: title, status, context, decision, consequences.

When reviewing an ADR, consider:

- **Status coherence** — is the status (`Proposed`, `Accepted`, `Superseded`) consistent with the current state of the codebase?
- **Decision clarity** — is the decision stated in one or two sentences, distinct from the context and rationale?
- **Consequences** — are both trade-offs and risks named, not just the benefits?
- **Coverage** — if an architectural change exists in the code but has no ADR, note the gap (Policy 002 requires an ADR before architecture changes)
- **Superseded links** — if an ADR supersedes a previous one, the old ADR should reference the new one

## Avoid

- Blocking work because a spec is missing — Policy 001 is advisory; note the gap once and move on
- Rewriting specs or ADRs for style; structure and completeness matter, prose elegance does not
- Treating these documents as executable contracts; they are guidance and records, not enforcement gates
- Proposing edits to `specs/template/` files in host repos
