# Documentation Review

## When to use

- Reviewing or editing a README, setup guide, or user-facing doc
- Assessing `docs/` content for accuracy after code or infra changes
- Checking whether a guide's commands still work (e.g., after toolchain changes)

## What to look for

- **Accuracy vs. the code** — verify commands, file paths, and config keys against current source; stale docs are worse than no docs
- **Executable examples** — prefer commands a reader can copy and run without mental translation; flag pseudocode presented as real commands
- **Platform alignment** — this repo targets Windows + Make; confirm `docs/windows_setup/` content and PowerShell paths are consistent with current scripts and `make` targets
- **Broken or relative links** — check that file references and cross-doc links resolve from the repo root
- **Audience fit** — consider who will read it (contributor, operator, new engineer) and whether the level of detail matches
- **Terminology consistency** — prefer the terms already used elsewhere in the repo rather than introducing new synonyms

## Quality signals

A good doc is scannable (headers, short bullets, concrete examples), accurate enough that following it produces the expected result, and scoped to what the reader needs to act — not an exhaustive reference. Thin, correct docs beat long, stale ones.

## Avoid

- Rewriting for style alone; accuracy and clarity outrank prose elegance
- Imposing a rigid structure on docs that are working fine as-is
- Reproducing what the code already shows clearly — link to the source instead
- Flagging missing sections that are genuinely out of scope for that doc
- Treating this skill as a gate — note observations and let the author decide
