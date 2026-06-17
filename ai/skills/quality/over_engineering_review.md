# Over-Engineering Review

## When to use

- Reviewing a diff or PR for unnecessary complexity
- Auditing a file or module when a user asks "what can I delete?", "is this over-engineered?", or "find the bloat"
- As a complement to `code_review_comments.md` — that skill covers correctness; this one covers complexity

This skill is a distinct lens, not a replacement for correctness review.

## Format

One line per finding:

```
L<line>: <tag> <what>. <replacement>.
```

For multi-file diffs:

```
<file>:L<line>: <tag> <what>. <replacement>.
```

End with the only metric that matters: `net: -<N> lines possible.`

If there is nothing to cut: `Lean already. Ship.`

## Tags

| Tag | Meaning | Replacement |
|---|---|---|
| `delete:` | Dead code, unused flexibility, speculative feature | Nothing — delete it |
| `stdlib:` | Hand-rolled thing the standard library ships | Name the stdlib function |
| `native:` | Dependency or code doing what the platform already does | Name the platform feature |
| `yagni:` | Abstraction with one implementation, config nobody sets, layer with one caller | Inline it until a second one exists |
| `shrink:` | Same logic, fewer lines | Show the shorter form |

## Examples

```
❌ "This validator class might be more complex than needed — have you considered
    whether all these rules are required at this stage?"

✅ L12-38: stdlib: 27-line email validator. "@" in email, 1 line — real validation is the confirmation mail.
```

```
✅ L4: native: moment.js imported for one date format. Use Intl.DateTimeFormat, 0 deps.
```

```
✅ repo.py:L88: yagni: AbstractRepository with one implementation. Inline until a second exists.
```

```
✅ L52-71: delete: retry wrapper around an idempotent local call. Nothing replaces it.
```

```
✅ L30-44: shrink: manual loop builds dict. dict(zip(keys, values)), 1 line.
```

## What to hunt

- Dependencies the stdlib or platform already ships
- Single-implementation interfaces and abstract base classes
- Factories with one product
- Wrappers that only delegate
- Files or classes that export one thing
- Dead flags and config keys nobody sets
- Hand-rolled versions of `itertools`, `functools`, `pathlib`, `dataclasses`, etc.

## Boundaries

- **Complexity only.** Correctness bugs, security holes, and performance problems go to `code_review_comments.md`.
- A single smoke test or `assert`-based self-check is the minimum floor — never flag it for deletion.
- Does not apply fixes — lists findings only.
- A single deliberate simplification marked with `# debt:` (ceiling + upgrade trigger) is not bloat.

## See also

- [code_review_comments.md](../docs/code_review_comments.md) — correctness review (bugs, risks, nits)
- [simplicity.md](./simplicity.md) — the decision ladder for writing code
- [debt_ledger.md](./debt_ledger.md) — harvesting `# debt:` markers left by deliberate shortcuts
