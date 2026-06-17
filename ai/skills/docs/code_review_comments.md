# Code Review Comments

## When to use

- Writing comments on a PR diff or file review
- Structuring feedback before posting it to a code review tool
- Assessing a diff as part of a broader task (pairs with `spec_adr_review` for specs and ADRs)

This skill shapes *how* to write review comments — it is not a gate. Apply it alongside the
primary review, not instead of it.

## Format

One line per finding:

```
L<line>: <problem>. <fix>.
```

For multi-file diffs:

```
<file>:L<line>: <problem>. <fix>.
```

**Severity prefix** (include when the diff mixes severity levels):

| Prefix | Use for |
|---|---|
| `🔴 bug:` | Wrong output, crash, security hole, data loss |
| `🟡 risk:` | Edge case, race, missing guard, swallowed error, perf cliff |
| `🔵 nit:` | Style, naming, micro-optimisation — author can ignore |
| `❓ q:` | Genuine question before judging, not a suggestion |

## Rules

**Keep:**
- Exact line numbers
- Symbol and function names in backticks
- A concrete fix, not "consider refactoring this"
- The *why* when the fix is not obvious from the problem statement alone

**Drop:**
- "I noticed that…", "It seems like…", "You might want to consider…"
- "This is just a suggestion but…" — use `🔵 nit:` instead
- Per-comment praise ("Great work on this line!")
- Restating what the line does — the reviewer can read the diff
- Hedging ("perhaps", "maybe", "I think") — if genuinely unsure, use `❓ q:`

## Examples

Bug with guard missing:
```
❌ "I noticed that on line 42 you're not checking if the user object is null before
    accessing the email property. This could potentially cause a crash. You might
    want to add a null check here."

✅ L42: 🔴 bug: user can be null after .find(). Add guard before .email.
```

Overgrown function:
```
❌ "It looks like this function is doing a lot of things and might benefit from
    being broken up into smaller functions for readability."

✅ L88-140: 🔵 nit: 50-line fn does 4 things. Extract validate/normalise/persist.
```

Missing retry:
```
❌ "Have you considered what happens if the API returns a 429? I think we should
    probably handle that case."

✅ L23: 🟡 risk: no retry on 429. Wrap in withBackoff(3).
```

## Auto-Clarity

Drop the terse format for:
- Security findings of CVE class — write a plain-English paragraph with a reference before the one-liner fix
- Architectural disagreements — rationale cannot fit in one line; write a paragraph, then resume
- Onboarding contexts where the author is new and needs the *why* explained

Resume one-line format after the expanded section.

## Avoid

- Big-refactor proposals in review comments — note the concern, open a separate issue
- Guessing intent when more context is needed — use `❓ q:` and cite the line
- Formatting nits unless they change meaning or break a linter rule the repo enforces
- Approving or requesting-changes programmatically — this skill only drafts the comments

## See also

- [`spec_adr_review.md`](./spec_adr_review.md) — for reviewing specs and ADRs
- [`doc_review.md`](./doc_review.md) — for reviewing README and prose documentation
