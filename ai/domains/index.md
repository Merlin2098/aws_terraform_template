# Domain Index

Navigation map for all skill domains in this framework.
This file complements `ai/skills.yaml` (authoritative slug index) with semantic grouping by domain.

---

## How to use this index

1. Identify the domain of your task from the table below.
2. Find the relevant skill file(s).
3. Check `ai/skills.yaml` for the canonical slug to use in references.
4. For cross-domain tasks, consult skills from each relevant domain.

---

## Domain Map

### Data Product — [descriptor](data-product.md)

Core data engineering: ingestion, transformation, serving, analytics, and storage.

| Skill | Path |
|---|---|
| ETL patterns (Bronze/Silver/Gold) | `ai/skills/data/etl_patterns.md` |
| Data contracts | `ai/skills/data/data_contracts.md` |
| Data quality | `ai/skills/data/data_quality_guidance.md` |
| Athena query patterns | `ai/skills/data/athena_patterns.md` |
| SQL workflow | `ai/skills/sql/sql_workflow_guidance.md` |

---

### AWS — [descriptor](aws.md)

Managed cloud services: compute, storage, messaging, ML, security.

| Skill | Path |
|---|---|
| Lambda functions | `ai/skills/aws/lambda_functions.md` |
| S3 data lake | `ai/skills/aws/s3_data_lake.md` |
| S3 presigned URLs | `ai/skills/aws/s3_presigned_urls.md` |
| SQS patterns | `ai/skills/aws/sqs_patterns.md` |
| Step Functions | `ai/skills/aws/step_functions.md` |
| EventBridge | `ai/skills/aws/eventbridge.md` |
| API Gateway | `ai/skills/aws/api_gateway.md` |
| CloudFront + S3 hosting | `ai/skills/aws/cloudfront_s3_hosting.md` |
| CloudWatch logging | `ai/skills/aws/cloudwatch_logging.md` |
| Glue jobs | `ai/skills/aws/glue_jobs.md` |
| Textract | `ai/skills/aws/textract.md` |
| Bedrock permissions | `ai/skills/aws/bedrock_permissions.md` |
| Cognito auth | `ai/skills/aws/cognito_auth.md` |
| IAM policies | `ai/skills/aws/iam_policies.md` |
| Smoke testing | `ai/skills/aws/aws_smoke_testing.md` |

---

### Terraform — [descriptor](terraform.md)

Infrastructure as code: modules, state, CI/CD, security, governance.

| Skill | Path |
|---|---|
| Style conventions | `ai/skills/terraform/terraform_style.md` |
| Modules | `ai/skills/terraform/modules.md` |
| State management | `ai/skills/terraform/state_management.md` |
| IAM least privilege | `ai/skills/terraform/iam_least_privilege.md` |
| Testing | `ai/skills/terraform/terraform_testing.md` |
| Mocks | `ai/skills/terraform/terraform_mocks.md` |
| CI/CD | `ai/skills/terraform/terraform_ci_cd.md` |
| Refactoring | `ai/skills/terraform/terraform_refactoring.md` |
| Stacks | `ai/skills/terraform/terraform_stacks.md` |
| Orchestration | `ai/skills/terraform/terraform_orchestration.md` |
| Import (manual) | `ai/skills/terraform/terraform_import_manual.md` |
| Import (discovery) | `ai/skills/terraform/terraform_import_discovery.md` |
| Security | `ai/skills/terraform/terraform_security.md` |
| Observability | `ai/skills/terraform/terraform_observability.md` |
| Governance | `ai/skills/terraform/terraform_governance.md` |
| Environment promotion | `ai/skills/terraform/environment_promotion.md` |

---

### Python — [descriptor](python.md)

Backend code patterns: project structure, testing, error handling, logging, ML clients.

| Skill | Path |
|---|---|
| Project guidance | `ai/skills/python/python_project_guidance.md` |
| Testing quality | `ai/skills/python/python_testing_quality.md` |
| Bedrock client | `ai/skills/python/bedrock_client.md` |
| Error handling (pipeline) | `ai/skills/python/error_handling_pipeline.md` |
| Structured logging | `ai/skills/python/logging_structured.md` |

---

### Frontend (AWS-integrated) — [descriptor](frontend.md)

React SPA patterns deployed to AWS (S3 + CloudFront).

| Skill | Path |
|---|---|
| React + Vite + AWS deploy | `ai/skills/frontend/react_vite_aws.md` |
| API client patterns | `ai/skills/frontend/api_client_patterns.md` |
| File upload UX | `ai/skills/frontend/file_upload_ux.md` |

---

### SaaS — [descriptor](saas.md)

Full-stack SaaS applications: React, FastAPI, PostgreSQL/Supabase, Auth, Analytics, Deploy.

| Skill | Path |
|---|---|
| Frontend (React + Tailwind) | `ai/skills/saas/frontend.md` |
| Backend (FastAPI) | `ai/skills/saas/backend.md` |
| Database (PostgreSQL/Supabase) | `ai/skills/saas/database.md` |
| Authentication (Supabase Auth + RBAC) | `ai/skills/saas/auth.md` |
| SaaS Analytics | `ai/skills/saas/analytics.md` |
| Deployment (Railway/Vercel) | `ai/skills/saas/deployment.md` |
| UX/UI | `ai/skills/saas/ux.md` |
| Supabase Storage & RLS | `ai/skills/saas/supabase.md` |
| VPS Deployment (Docker/Nginx/SSL) | `ai/skills/saas/vps.md` |
| Domains, DNS & Email | `ai/skills/saas/domains.md` |

---

### Documentation

Review guidance for prose docs, specs, architectural decision records, commits, and code review.

| Skill | Path |
|---|---|
| README and docs review | `ai/skills/docs/doc_review.md` |
| Spec and ADR review | `ai/skills/docs/spec_adr_review.md` |
| Commit messages | `ai/skills/docs/commit_messages.md` |
| Code review comments | `ai/skills/docs/code_review_comments.md` |

---

### Shell / Scripting — [descriptor](shell.md)

Bash and PowerShell script generation, validation, and maintenance for Windows,
Linux, WSL, and Git Bash environments.

| Skill | Path |
|---|---|
| Environment detection | `ai/skills/shell/environment_detection.md` |
| PowerShell core | `ai/skills/shell/powershell_core.md` |
| PowerShell filesystem | `ai/skills/shell/powershell_filesystem.md` |
| PowerShell Windows admin (services, registry, scheduled tasks) | `ai/skills/shell/powershell_windows_admin.md` |
| PowerShell JSON/YAML | `ai/skills/shell/powershell_json_yaml.md` |
| Bash core | `ai/skills/shell/bash_core.md` |
| CLI automation (git, terraform, docker, aws, az) | `ai/skills/shell/cli_automation.md` |
| Script security | `ai/skills/shell/script_security.md` |
| Script quality (testing, documentation, refactoring) | `ai/skills/shell/script_quality.md` |

---

### Quality / Simplicity

Behavioral skills that change how the agent approaches a task: a decision ladder,
a complexity review lens, and a deliberate-shortcut convention.

| Skill | Path |
|---|---|
| Simplicity ladder | `ai/skills/quality/simplicity.md` |
| Over-engineering review | `ai/skills/quality/over_engineering_review.md` |
| Debt ledger (`# debt:` convention + harvest) | `ai/skills/quality/debt_ledger.md` |

---

## Global Policies

All domains are subject to the policies in [`ai/policies/global.md`](../policies/global.md).

---

## Adding a New Domain

1. Create `ai/skills/<domain>/` with skill files following the recipe format.
2. Register each skill in `ai/skills.yaml` with a unique slug.
3. Add a row block for the domain in this file.
4. If the domain is large, create `ai/domains/<domain>.md` as a dedicated descriptor.
5. Register each skill in `ai/skills.yaml` and add a row in this index for the new domain.
6. Add the new path to `ai/context.yaml` under `structure.guidance`.
