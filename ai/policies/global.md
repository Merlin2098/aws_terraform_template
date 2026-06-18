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

---

## Policy 006 — Auto-Clarity When Compressing Output

**Level:** Advisory

When compressing or abbreviating output (terse commit subjects, one-line review comments,
brief responses), always revert to full prose for:

- Security warnings
- Confirmations of irreversible actions (destructive Terraform operations, data migrations, drops)
- Multi-step sequences where omitting conjunctions or step order risks misreading

Resume terse style after the critical section is complete.

**Agent behaviour:** Apply this rule automatically whenever a skill or user instruction requests
brevity. Do not require an explicit reminder.

---

## Policy 007 — Never Send Sensitive Files to External Services

**Level:** Required

Never pass credentials, keys, or secrets to external APIs, compression tools, or any
third-party service boundary. This includes:

- `.env` files and variants (`.env.local`, `.env.production`, …)
- Private key files (`.pem`, `.key`, `.p12`, `.pfx`, `.asc`, `.gpg`)
- Files named `credentials`, `secrets`, `passwords`, or similar
- Content from `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.kube`, `~/.docker`

This constraint applies regardless of the tool or automation in use. When a task would require
sending file content to an external service, refuse and explain the risk.

---

## Policy 008 — Prefer the Simplest Working Solution

**Level:** Advisory

Before writing new code, adding a dependency, or introducing an abstraction, apply the
simplicity ladder in `ai/skills/quality/simplicity.md`:

1. Does this need to exist at all? (YAGNI)
2. Does the stdlib do it?
3. Does a native platform feature cover it?
4. Does an already-installed dependency solve it?
5. Can it be one line?
6. Only then: the minimum code that works.

Stop at the first rung that holds.

**When to apply:** any implementation task — feature, refactor, new dependency, new file.

**Agent behaviour:** apply the ladder silently; only surface the reasoning if a
simplification was non-obvious or if an alternative was skipped. Do not block the task.

**Exceptions:** never simplify away input validation at trust boundaries, error handling
that prevents data loss, security controls, mandatory tags and log retention (SPEC-009),
or anything the user explicitly requested. Cross-ref Policy 006 (Auto-Clarity) for when
to revert to full prose.

**Deliberate shortcuts:** a simplification with a known ceiling gets a `# debt:` comment
naming the ceiling and upgrade trigger. See `ai/skills/quality/debt_ledger.md`.

---

## Policy 009 — AWS/Terraform Operational Guardrails (SPEC-009)

**Level:** Required

Applies when the project profile enables `aws` or `terraform` capabilities.
Full specification: `specs/template/009-cloud-observability-guardrails.md`.
Script structure and templates: `ai/skills/aws/aws_smoke_testing.md`.

### The agent MUST

- declare `aws_cloudwatch_log_group` explicitly for every service that produces logs
- set `retention_in_days` on every log group — never omit it
- include `aws_budgets_budget` when deploying any environment
- apply `local.common_tags` (including `CostCenter`) to every resource
- expose `log_group_name`, `log_group_arn`, and `resource_arn` as outputs in every module
- generate `tests/aws/` Python/boto3 validation tests when deploying AWS infrastructure
  (see `ai/skills/aws/aws_smoke_testing.md` for structure and templates)
- validate IAM roles before applying infrastructure changes

### The agent MUST NOT

- delete or overwrite `terraform.tfstate`
- enable S3 versioning by default — only when explicitly requested and justified
- assume implicit IAM permissions — all permissions must be declared in Terraform
- create resources without mandatory tags
- omit `retention_in_days` on CloudWatch log groups

---

## Policy 010 — IAM Cross-Module Placement Rule

**Level:** Required

Applies when the project profile enables `aws` or `terraform` capabilities.

When a resource in module A requires a permission whose target ARN is only known
inside module B, declare the `aws_iam_role_policy` in module B (where the ARN is
available), not in module A. Placing it in module A would require passing the ARN
back and creates a circular dependency.

**Canonical example — Lambda DLQ:**
The `aws_sqs_queue` (DLQ) lives in the `lambda` module. AWS validates
`sqs:SendMessage` on that ARN at function creation time. Therefore the inline
policy granting `sqs:SendMessage` must be declared in the `lambda` module,
attached to the execution role name received as a variable — not in the `iam`
module.
