# AGENTS.md

## Purpose

This file defines the working contract for AI agents in the current project.
It is intentionally project-name agnostic so it remains valid when copied into
or used to bootstrap another repository.

Agents should first inspect the repository and its active capabilities before
assuming a language, cloud provider, framework, or infrastructure stack.
Typical supported work may include:

* Python data jobs and helpers
* SQL transformations
* Terraform infrastructure
* Application and frontend code
* Config-driven workflows
* Lightweight testing and packaging workflows

---

## Knowledge Sources

Use:

* `ai/skills/` for patterns and best practices
* `ai/skills.yaml` as the authoritative skills index
* `ai/domains/index.md` for domain-based navigation across all skill areas
* `ai/policies/global.md` for cross-domain policies (advisory and required)
* `ai/context.yaml` as the authoritative AI context-generation configuration
* `.template-profile.yaml` for active project capabilities and dependency policy
* `specs/template/` for inherited contracts when that directory is present
* `specs/project/` for project-authored specs when that directory is present

These files are project guidance and configuration inputs.
They are not executable orchestration logic.

---

## Working Style

When assisting in a project that contains this guidance:

1. Understand the objective and current repository shape
2. Search for existing implementations before proposing new files
3. Identify relevant skills from `ai/skills/`
4. Apply patterns as guidance, not as rigid rules
5. Prefer simple, explicit changes over frameworks or abstractions
6. Validate the result against repository principles and documented workflows

---

## Skill Usage

The agent should:

* discover relevant skills automatically from `ai/skills/`
* treat `ai/skills.yaml` and `ai/context.yaml` as the source of truth for AI guidance inputs
* match tasks with skill names such as `testing`, `ci_cd`, `mocks`, `glue`, or `terraform`
* use skills to guide implementation without requiring explicit invocation by the user

The agent must not:

* require explicit skill invocation
* enforce rigid one-to-one mappings between tasks and skills
* create skill composition or orchestration logic

---

## Execution Rules

Use explicit project commands only.

Preferred workflow:

* use `make <target>` when `make` is available
* in restricted Windows environments, use `scripts/windows/run_make.ps1` or the documented wrapper flow under `docs/windows_setup/`
* run Terraform commands directly and intentionally from `infra/`

Do not introduce hidden automation.

---

## Package Manager Awareness

Projects using this guidance use `uv` for Python dependency management.

The agent should:

* inspect `.template-profile.yaml`, `pyproject.toml`, and `uv.lock`
* resolve active dependency extras and groups from the project profile
* use the repository's documented `uv` wrappers or explicit `uv` commands
* keep packaging, testing, and environment guidance aligned with the active capabilities

---

## Approval Boundaries

### Never without approval

* `terraform apply`
* `terraform destroy`
* modify infrastructure state
* overwrite data or generated artifacts intentionally owned by users

### Ask before

* IAM changes
* Terraform module changes
* paid AWS services or production-grade infrastructure defaults
* data contract updates
* budget limit or alert email changes
* CloudWatch log group deletion or retention reduction

---

## Principles

* separation of concerns across infra, code, and config
* SQL separate from Python
* config-driven pipelines
* contracts-first validation
* Terraform should optimize for destroyability, low-cost dev environments, reproducibility, and explicit resource ownership
* prefer simple over complex
* keep workflows explicit and reproducible

---

## Constraints

The agent must not:

* create orchestration frameworks
* define skill composition systems
* introduce meta-systems
* recreate hidden framework-like behavior

---

## Existing Code Awareness

Before generating any new file or artifact, the agent must:

1. search the repository for existing implementations
2. prefer modifying or extending existing files over creating new ones
3. avoid duplicating Terraform modules, ETL jobs, SQL transformations, or config files

If similar functionality already exists, reuse or refactor it instead of
creating parallel structures.

Only create new files when:

* no equivalent exists
* or the user explicitly requests it

---

## Skill Trigger Map

The map below is indicative, not exhaustive. If a task does not appear here,
follow the discovery flow in *Skill Usage*.

| When the task involves… | Consult |
|---|---|
| Designing or editing a Python ETL job | `ai/skills/data/etl_patterns.md`, `ai/skills/python/python_project_guidance.md` |
| OCR normalisation, invoice extraction, LLM document processing | `ai/skills/data/etl_patterns.md`, `ai/skills/python/bedrock_client.md`, `ai/skills/aws/textract.md` |
| Validation or data quality (Python/SQL/AWS) | `ai/skills/data/data_quality_guidance.md`, `ai/skills/data/data_contracts.md` |
| Athena queries, partition pruning, query cost | `ai/skills/data/athena_patterns.md`, `ai/skills/sql/sql_workflow_guidance.md` |
| Python tests | `ai/skills/python/python_testing_quality.md` |
| Python pipeline error handling, Step Functions exceptions | `ai/skills/python/error_handling_pipeline.md`, `ai/skills/aws/step_functions.md` |
| Python structured logging, CloudWatch Insights | `ai/skills/python/logging_structured.md`, `ai/skills/aws/cloudwatch_logging.md` |
| Bedrock invocation, model access, throttling | `ai/skills/python/bedrock_client.md`, `ai/skills/aws/bedrock_permissions.md` |
| New SQL or transformation refactor | `ai/skills/sql/sql_workflow_guidance.md` |
| AWS Glue (jobs, crawlers, catalog) | `ai/skills/aws/glue_jobs.md` |
| AWS Lambda | `ai/skills/aws/lambda_functions.md`, `ai/skills/aws/iam_policies.md` |
| Step Functions orchestration | `ai/skills/aws/step_functions.md` |
| Scheduling / event-driven | `ai/skills/aws/eventbridge.md` |
| SQS queues, DLQs, Lambda event source mapping | `ai/skills/aws/sqs_patterns.md`, `ai/skills/aws/lambda_functions.md` |
| Textract document analysis | `ai/skills/aws/textract.md`, `ai/skills/aws/sqs_patterns.md` |
| API Gateway endpoints, CORS, throttling, authorisers | `ai/skills/aws/api_gateway.md`, `ai/skills/aws/lambda_functions.md` |
| User authentication, Cognito, JWT | `ai/skills/aws/cognito_auth.md`, `ai/skills/aws/api_gateway.md` |
| S3 presigned URLs, direct browser upload | `ai/skills/aws/s3_presigned_urls.md`, `ai/skills/frontend/file_upload_ux.md` |
| CloudFront + S3 static hosting, OAC, cache invalidation | `ai/skills/aws/cloudfront_s3_hosting.md` |
| S3 / data lake storage | `ai/skills/aws/s3_data_lake.md` |
| AWS logging / observability | `ai/skills/aws/cloudwatch_logging.md`, `ai/skills/terraform/terraform_observability.md` |
| IAM (policies, roles) | `ai/skills/aws/iam_policies.md`, `ai/skills/terraform/iam_least_privilege.md` |
| Bedrock IAM, model ARN scoping, cross-region inference | `ai/skills/aws/bedrock_permissions.md`, `ai/skills/terraform/iam_least_privilege.md` |
| Smoke testing AWS resources | `ai/skills/aws/aws_smoke_testing.md` |
| Tagging, budgets, per-service cost, drift management | `ai/skills/terraform/terraform_governance.md` |
| Writing or refactoring Terraform | `ai/skills/terraform/terraform_style.md`, `ai/skills/terraform/modules.md` |
| Terraform state / backends | `ai/skills/terraform/state_management.md` |
| Terraform tests / mocks | `ai/skills/terraform/terraform_testing.md`, `ai/skills/terraform/terraform_mocks.md` |
| Terraform CI/CD | `ai/skills/terraform/terraform_ci_cd.md`, `ai/skills/terraform/terraform_orchestration.md` |
| Importing existing resources | `ai/skills/terraform/terraform_import_manual.md`, `ai/skills/terraform/terraform_import_discovery.md` |
| Module refactor / multi-env / environment promotion | `ai/skills/terraform/environment_promotion.md`, `ai/skills/terraform/terraform_refactoring.md`, `ai/skills/terraform/terraform_stacks.md` |
| Infra security review | `ai/skills/terraform/terraform_security.md` |
| Frontend React + Vite build, deploy, env vars | `ai/skills/frontend/react_vite_aws.md`, `ai/skills/aws/cloudfront_s3_hosting.md` |
| Frontend API client, auth headers, retries, error handling | `ai/skills/frontend/api_client_patterns.md`, `ai/skills/aws/api_gateway.md` |
| Frontend file upload, drag-and-drop, upload progress | `ai/skills/frontend/file_upload_ux.md`, `ai/skills/aws/s3_presigned_urls.md` |
| SaaS React + Tailwind UI components, hooks, forms | `ai/skills/saas/frontend.md` |
| SaaS FastAPI endpoints, service layer, repository pattern | `ai/skills/saas/backend.md` |
| SaaS PostgreSQL schema, Alembic migrations, soft delete | `ai/skills/saas/database.md` |
| SaaS Supabase Auth, JWT validation, RBAC roles | `ai/skills/saas/auth.md` |
| SaaS KPI dashboards, business metrics, snapshot tables | `ai/skills/saas/analytics.md` |
| SaaS Railway / Vercel deploy, GitHub Actions CI/CD | `ai/skills/saas/deployment.md` |
| SaaS dashboard UX, form flows, navigation, accessibility | `ai/skills/saas/ux.md` |
| Reviewing README, docs, setup guides, or user-facing prose | `ai/skills/docs/doc_review.md` |
| Reviewing specs or ADRs | `ai/skills/docs/spec_adr_review.md`, `ai/policies/global.md` |
| Writing a git commit message | `ai/skills/docs/commit_messages.md` |
| Writing PR or code review comments | `ai/skills/docs/code_review_comments.md`, `ai/skills/docs/spec_adr_review.md` |
| Simplest / minimal / laziest solution, adding a dependency or abstraction | `ai/skills/quality/simplicity.md` |
| Over-engineering review, "what can I delete", complexity audit | `ai/skills/quality/over_engineering_review.md` |
| Harvest deferred shortcuts, "show the debt ledger", `# debt:` markers | `ai/skills/quality/debt_ledger.md` |

---

## AI Agent Operational Policies (SPEC-009)

These rules apply when the project enables AWS or Terraform capabilities.

### The agent MUST

* declare `aws_cloudwatch_log_group` explicitly for every service that produces logs
* set `retention_in_days` on every log group — never omit it
* include `aws_budgets_budget` when deploying any environment
* apply `local.common_tags` (including `CostCenter`) to every resource
* expose `log_group_name`, `log_group_arn`, and `resource_arn` as outputs in every module
* generate `tests/aws/` validation scripts when deploying AWS infrastructure
  (see `ai/skills/aws/aws_smoke_testing.md` for structure and templates)
* validate IAM roles before applying infrastructure changes

### The agent MUST NOT

* delete or overwrite `terraform.tfstate`
* enable S3 versioning by default — only when explicitly requested and justified
* assume implicit IAM permissions — all permissions must be declared in Terraform
* create resources without mandatory tags
* omit `retention_in_days` on CloudWatch log groups

### IAM cross-module rule

When a resource in module A requires a permission whose target ARN is only known
inside module B, declare the `aws_iam_role_policy` in module B (where the ARN is
available), not in module A. Placing it in module A would require passing the ARN
back and create a circular dependency.

**Canonical example — Lambda DLQ:**
The `aws_sqs_queue` (DLQ) lives in the `lambda` module. AWS validates
`sqs:SendMessage` on that ARN at function creation time. Therefore the inline
policy granting `sqs:SendMessage` must be declared in the `lambda` module,
attached to the execution role name received as a variable — not in the `iam`
module.

### AWS project obligation

When deploying AWS resources, generate `tests/aws/` with:

```
tests/aws/
├── precheck/   # validate_iam.ps1, validate_tags.ps1, validate_budget.ps1, smoke_resources.ps1
├── smoke/      # smoke_s3.ps1, smoke_cloudwatch.ps1
├── logs/       # download_cloudwatch_logs.ps1, export_pipeline_outputs.ps1
├── gitbash/    # precheck.sh (bash equivalent for CI/Linux)
└── README.md
```

Scripts must read resource identifiers from `terraform output` — never hardcode names or ARNs.

---

## Philosophy

Simple. Explicit. Reproducible.

AI is a helper for the current project, not the system itself.

---

## Simplicity

Apply the simplicity ladder (see `ai/skills/quality/simplicity.md` and Policy 008)
to every implementation task. Stop at the first rung that holds:

1. Does this need to exist? (YAGNI)
2. Stdlib?
3. Native platform feature?
4. Already-installed dependency?
5. One line?
6. Minimum code.

**Deliberate shortcuts** — a simplification with a known ceiling — are marked inline:

```python
# debt: <ceiling>, <upgrade trigger>
```

Run `ai/skills/quality/debt_ledger.md` to harvest all markers into a ledger.
Never simplify away security controls, data-loss guards, or anything explicitly requested.
