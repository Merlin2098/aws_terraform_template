# Debt Ledger

## When to use

- Harvesting all deliberate shortcuts in the codebase into a single ledger
- Checking what has been deferred and whether any deferrals have gone stale
- When a user asks "what did we defer?", "list the shortcuts", or "show the debt ledger"

This skill is one-shot and read-only. It changes nothing.

## The `# debt:` convention

A deliberate shortcut with a known ceiling is marked at the point of the shortcut:

```
# debt: <ceiling>, <upgrade trigger>
```

- **Ceiling** — the limit of the current solution (throughput, scale, edge case it doesn't handle)
- **Upgrade trigger** — the observable condition that makes it worth revisiting

**Python / SQL / HCL (Terraform):** use `#`
**JavaScript / TypeScript:** use `//`

### Examples

```python
# debt: global lock, per-user locks if concurrent write throughput exceeds 100 rps
_lock = threading.Lock()
```

```sql
-- debt: full-table scan, add composite index on (tenant_id, created_at) if query > 500ms
SELECT * FROM events WHERE tenant_id = :tid ORDER BY created_at DESC LIMIT 50;
```

```hcl
# debt: single AZ for cost, add multi-AZ if this becomes a production workload
resource "aws_db_instance" "main" {
  multi_az = false
}
```

```typescript
// debt: naive retry, replace with exponential backoff if 429s appear in CloudWatch
const result = await fetch(url);
```

A `# debt:` comment without both a ceiling and an upgrade trigger is incomplete.
The harvest command will flag it with `no-trigger`.

## Harvest command

Run from the repo root, skipping generated and vendor directories:

```bash
grep -rnE '(#|//|--|;) ?debt:' . \
  --include="*.py" --include="*.sql" --include="*.tf" \
  --include="*.ts" --include="*.js" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.git \
  --exclude-dir=.venv --exclude-dir=__pycache__ \
  --exclude-dir=build --exclude-dir=dist
```

## Output format

One row per marker, grouped by file:

```
<file>:<line> — <what was simplified>. ceiling: <the limit>. upgrade: <the trigger>.
```

Flag incomplete markers:

```
<file>:<line> — no-trigger: marker found but no upgrade condition named.
```

End with a summary line: `<N> markers, <M> with no trigger.`

If no markers found: `No # debt: markers. Clean ledger.`

## Persisting the ledger

By default, report only to the conversation. To write the ledger to a file,
the user must explicitly ask: `save the debt ledger` or `write to DEBT.md`.
Default output file: `DEBT.md` at the repo root.

## Boundaries

- Read-only. Never modifies source files.
- Does not evaluate whether a shortcut is justified — that is the author's call.
- One-shot per invocation; does not re-scan automatically.

## See also

- [simplicity.md](./simplicity.md) — the decision ladder that produces `# debt:` markers
- [over_engineering_review.md](./over_engineering_review.md) — complexity review for diffs
