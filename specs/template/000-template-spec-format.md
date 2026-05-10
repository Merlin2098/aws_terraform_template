# Spec format

Reusable structure for any spec in this repo. Copy this file when starting a
new spec under `specs/project/` and fill the sections.

## Context

Why this spec exists. What problem or ambiguity it resolves. Keep it to a
short paragraph.

## Contract

What is guaranteed, expected, or required. Use bullets, tables, or short
declarative statements. Reference concrete file paths and identifiers.

## Invariants

Things that must remain true across changes. Examples: tags always include
`ManagedBy=Terraform`; the artifact bucket is always `force_destroy=true` in
dev; secrets never live in Terraform state.

## Out of scope

What this spec deliberately does not cover. Useful to prevent scope creep
and to point readers to other specs or skills.

## References

Links to source files, related specs, skills, or external docs.

## Avoid

- Long prose explanations of code that the code already shows.
- Duplicating principles from `docs/terra_principles.md`.
- Patterns or recipes — those belong in `ai/skills/`.
