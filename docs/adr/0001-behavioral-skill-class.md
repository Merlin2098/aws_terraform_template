# ADR 0001 — Introduce a Behavioral Skill Class

**Status:** Accepted

---

## Context

The framework's `ai/skills/` directory contains 58 *reference* skills: Markdown
files the agent reads to learn how to do something (IAM least-privilege, ETL
patterns, SQL workflow, etc.). These are static knowledge sources — they do not
alter how the agent approaches a task; they only inform what the agent writes.

An architectural analysis of the `reusable/ponytail` skill pack identified a
distinct species: *behavioral* skills — skills that change the agent's decision
process rather than its domain knowledge. The canonical example is a decision
ladder: an ordered heuristic the agent executes the same way every time ("stop
at the first rung that holds").

The framework already encodes simplicity preferences as prose in `AGENTS.md`
("prefer simple over complex", "no overengineering") but those phrases are
re-interpreted from scratch each time. A behavioral skill makes the same intent
deterministic, auditable, and cross-referenceable.

This is an architecture change (adding a new class of first-class artifact)
and therefore requires an ADR under Policy 002.

---

## Decision

Introduce a **behavioral skill** class, distinct from reference skills, under
`ai/skills/quality/`. Behavioral skills:

- Live in `ai/skills/` and are indexed in `ai/skills.yaml` exactly like
  reference skills (no separate registry, no runtime change).
- Use the same native Markdown format (no front-matter; `# Title`, `## When to
  use`, standard heading structure).
- Are activated by *discovery* (trigger phrases in the AGENTS.md Skill Trigger
  Map), not by persistent session state.
- Encode a *process* (a ladder, a tag vocabulary, a harvest command) rather
  than domain knowledge.
- Explicitly list "When NOT to apply" so the agent knows boundaries.

The first behavioral skill is `ai/skills/quality/simplicity.md` (the
simplicity ladder). Two companion skills — `over_engineering_review.md` and
`debt_ledger.md` — provide the complexity review lens and the `# debt:`
convention harvester respectively.

**What this is not:** a persistent always-on mode, a plugin, or a meta-system.
The agent discovers and applies these skills the same way it discovers every
other skill — through the Skill Trigger Map and the `ai/skills.yaml` registry.

---

## Consequences

**Positive:**
- Simplicity principles become deterministic (a ladder) rather than prose
  preferences (re-derived each session).
- The `# debt:` convention creates a grep-harvestable shortcut ledger with
  zero infrastructure.
- Over-engineering review has a dedicated, terse tag vocabulary orthogonal to
  the existing correctness tags in `code_review_comments.md`.
- No runtime change required; `skill_registry.py` already handles arbitrary
  skills.yaml entries.

**Neutral:**
- Adds a `quality/` domain folder to `ai/skills/`. Covered by existing
  `ai/context.yaml` glob — no config edit needed.
- Skills.yaml grows by 3 entries (< 5% increase).

**Negative / risks:**
- The behavioral/reference distinction is implicit (in the skill content) not
  enforced. A future `type: behavioral` field in skills.yaml (Phase 2, gated
  behind a second behavioral skill) would make it explicit.
- Behavioral skills require clear "When NOT to apply" sections or they
  over-reach. Mitigated by the `simplicity.md` guardrails section and
  Policy 008.
