# Global Policies

Policies that apply across all domains in this framework.

---

## Policy 001 — Spec Before Code

**Level:** Advisory (guideline, not a gate)

Before implementing a significant feature or architectural change, a spec is desirable. For small tasks, quick fixes, or exploratory work where the scope is clear, a spec is optional.

**When to apply:**
- New features affecting multiple components → create or reference a spec
- Significant refactors or domain additions → create a spec first
- Small bug fixes, config tweaks, one-file changes → spec not required

**Agent behaviour:** If a task appears significant and no spec exists, mention it once and offer to create one. Do not block the work.

---

## Policy 002 — ADR Before Architecture Change

**Level:** Required

Any decision that changes the overall architecture (adding a new service, replacing a technology, changing a data contract) must be recorded in an ADR under `docs/adr/` before implementation begins.

**Format:** Use the standard ADR template — title, status, context, decision, consequences.

---

## Policy 003 — Configuration Over Hardcoding

**Level:** Required

Values that differ between environments (URLs, bucket names, credentials, feature flags, thresholds) must live in configuration files or environment variables, never hardcoded in source.

**Applies to:** Python, SQL, Terraform variable defaults, frontend env files, CI/CD workflows.

---

## Policy 005 — Documentation Skills Are Always Active

**Level:** Advisory

The skills in `ai/skills/docs/` apply to any task that touches documentation files
(README, `docs/`, `specs/`, ADRs). Apply them without waiting for an explicit request.

**When to apply:**
- Editing or creating any `.md` file that is not a skill or policy file itself
- Reviewing specs or ADRs as part of a broader task
- Noticing that docs are stale relative to the current code or infrastructure

**Agent behaviour:** Apply observations from `doc_review` or `spec_adr_review` inline
as advisory notes. Do not block the primary task.

---

## Policy 004 — Security By Default

**Level:** Required

Every new resource, endpoint, or data store must be private and least-privilege from day one. Security must not be retrofitted.

**Concrete rules:**
- S3 buckets: block public access, use OAC for CloudFront
- IAM: explicit deny on unused actions; no wildcard resources in production
- APIs: authentication required; no unauthenticated endpoints without explicit justification
- Secrets: never in source code; use environment variables or AWS Secrets Manager
- Database: no direct production access; changes through migrations only
