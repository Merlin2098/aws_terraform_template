# Commit Messages

## When to use

- Writing or generating a commit message for any staged change
- Reviewing whether an existing commit message is clear and well-formed
- Advising on commit message conventions in the context of this repo

## Rules

**Subject line**

- Format: `<type>(<scope>): <imperative summary>` — `<scope>` is optional
- Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `build`, `ci`, `style`, `revert`
- Imperative mood: "add", "fix", "remove" — not "added", "adds", "adding"
- ≤50 characters when possible; hard cap 72
- No trailing period
- Match the capitalisation convention already visible in the project history (lowercase after the colon)

**Body (only when needed)**

- Omit the body when the subject is self-explanatory
- Include a body for: non-obvious *why*, breaking changes, migration notes, linked issues
- Wrap at 72 characters
- Bullets with `-`, not `*`
- Reference issues and PRs at the end: `Closes #42`, `Refs #17`
- Breaking changes: open with `BREAKING CHANGE:` on its own line

**What never goes in**

- "This commit does X" — the diff already says what
- "I", "we", "now", "currently"
- "As requested by…" — use a `Co-Authored-By` trailer instead
- Unsolicited AI attribution in the subject or body
- Emoji, unless the project convention requires it
- Restating the filename when the scope already says it

## Examples

Simple fix — subject only:
```
fix(auth): correct token expiry boundary condition
```

New feature with non-obvious reasoning:
```
feat(api): add GET /users/:id/profile

Mobile client needs profile data without the full user payload
to reduce LTE bandwidth on cold-launch screens.

Closes #128
```

Breaking change:
```
feat(api)!: rename /v1/orders to /v1/checkout

BREAKING CHANGE: clients on /v1/orders must migrate to /v1/checkout
before 2026-06-01. Old route returns 410 after that date.
```

## Avoid

- Subject lines that restate the diff ("update file X", "change Y in Z")
- Bodies that explain *what* rather than *why* — the diff does that
- Skipping the body for breaking changes, security fixes, or data migrations — future debuggers need the context
- Mixing unrelated changes in one commit — split them instead
