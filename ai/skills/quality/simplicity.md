# Simplicity Ladder

## When to use

- Implementing a feature, adding a dependency, or introducing an abstraction
- Reviewing your own proposed change before writing it
- Any time the task could plausibly be solved with less code
- When a user asks for the "simplest", "minimal", or "laziest" solution

## The ladder (stop at the first rung that holds)

1. **Does this need to exist at all?** Speculative need → skip it, say so in one line. (YAGNI)
2. **Does the stdlib do it?** Use it.
3. **Does a native platform feature cover it?** (Terraform builtin, AWS managed feature, SQL constraint over application code, `make` target over a script) Use it.
4. **Does an already-installed dependency solve it?** Use it. Never add a new dep for what a few lines do.
5. **Can it be one line?** One line.
6. **Only then:** the minimum code that works.

Two rungs both hold → take the higher one and move on. The first solution that
works at the highest rung is the right one.

## Output pattern

Code first. Then at most two short lines: what was skipped and when to add it.

Pattern: `[solution] → skipped: [X], add when [Y].`

If no shortcut was taken, no explanation needed.

## When NOT to simplify

Never simplify away:

- Input validation at trust boundaries (user input, external APIs)
- Error handling that prevents data loss
- Security controls and IAM least-privilege (Policy 004)
- Mandatory tags, log groups, and log retention (SPEC-009)
- Anything explicitly requested by the user — if overridden, build it, no re-arguing

## Marking deliberate shortcuts

A shortcut with a known ceiling gets a `# debt:` comment naming the ceiling
and the upgrade trigger. This keeps deferrals visible and harvestable.

```python
# debt: global lock, per-user locks if concurrent write throughput exceeds N rps
results = cache.get(key)
```

See `ai/skills/quality/debt_ledger.md` for the full convention and harvest command.

## Avoid

- Re-arguing a simplification the user explicitly overrode
- Picking the flimsier algorithm to save lines — fewer lines is not weaker logic
- Unrequested abstractions: no interface with one implementation, no factory for
  one product, no config for a value that never changes
- Boilerplate or scaffolding "for later" — later can scaffold for itself

## See also

- [over_engineering_review.md](./over_engineering_review.md) — complexity review lens for diffs
- [debt_ledger.md](./debt_ledger.md) — `# debt:` convention and harvest command
- [ai/policies/global.md](../../policies/global.md) Policy 008 — Prefer the Simplest Working Solution
- [ai/policies/global.md](../../policies/global.md) Policy 006 — Auto-Clarity (when to revert to full prose)
