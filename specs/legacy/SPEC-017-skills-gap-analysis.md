# SPEC-017: Skills Gap Analysis — Recommended AI Guidance Skills

**Date:** 2026-06-02
**Status:** Proposed
**Author:** Claude (automated analysis)

---

## Purpose

This document identifies AI guidance skills (`ai/skills/`) that would benefit
this project and similar cloud-first AWS data engineering pipelines. Skills are
grouped by domain. Each entry explains the gap and the concrete value the skill
would provide.

Skills already present in `ai/skills/` are excluded from this list.

---

## Current Skills Inventory

| Domain     | Count | Skills present |
|------------|-------|----------------|
| AWS        | 7     | glue_jobs, lambda_functions, step_functions, eventbridge, s3_data_lake, iam_policies, cloudwatch_logging |
| Terraform  | 13    | terraform_style, modules, state_management, iam_least_privilege, terraform_testing, terraform_mocks, terraform_ci_cd, terraform_refactoring, terraform_stacks, terraform_orchestration, terraform_import_manual, terraform_import_discovery, terraform_security |
| Data       | 3     | data_contracts, data_quality_guidance, etl_patterns |
| Python     | 2     | python_project_guidance, python_testing_quality |
| SQL        | 1     | sql_workflow_guidance |

**Total:** 26 skills across 5 domains.

---

## Identified Gaps

---

## 1. Infrastructure (`infra/`)

### 1.1 `terraform/cost_management`
**Gap:** The project already declares `infra/envs/dev/budget.tf`. There is no
guidance on tagging strategy for cost allocation, AWS Budgets alarms, or how
to design Terraform modules so cost-relevant resources are identifiable.

**Value:** Prevents accidental runaway spend on Textract, Bedrock, and Glue
in a dev environment. Provides patterns for Cost Explorer queries aligned to
project tags.

**Key topics:**
- AWS Budgets resource (`aws_budgets_budget`) with Terraform
- Mandatory cost-allocation tags (Project, Environment, CostCenter)
- Alerts before and at threshold (80 % / 100 %)
- Forecast-based vs. actual-spend alarms
- Per-service budget breakdown (Bedrock, Textract, Glue, S3)

---

### 1.2 `terraform/environment_promotion`
**Gap:** The repo has a single `envs/dev/` folder. There are no guidelines for
promoting infrastructure through dev → staging → prod, or for keeping module
interfaces stable across environments.

**Value:** When MVP2 lands (see `specs/product/MVP2-definition.md`) a staging
environment will be needed. Having a documented promotion path prevents
copy-paste drift.

**Key topics:**
- Workspace vs. directory-per-environment trade-offs
- Variable override files per environment (`terraform.tfvars`)
- Immutable artifact promotion (Lambda packages, Glue scripts)
- State isolation between environments

---

### 1.3 `aws/api_gateway`
**Gap:** The project exposes Lambda-backed REST APIs (`chat_api.tf`,
`web_api.tf`) but has no skill covering API Gateway patterns, throttling,
CORS configuration, or authoriser setup.

**Value:** The web portal and chat API (SPEC-010, SPEC-011) depend on
correctly configured API Gateway. Without guidance, CORS bugs and missing
throttle limits are the most common production failures.

**Key topics:**
- REST vs. HTTP API trade-offs (cost, features)
- Lambda proxy integration
- CORS configuration at the API and method level
- Usage plans and throttling
- API keys vs. Cognito vs. IAM authorisers
- CloudWatch access logging for API Gateway

---

### 1.4 `aws/textract`
**Gap:** AWS Textract is a first-class service in this pipeline
(`src/pipeline/ocr.py`, `infra/modules/textract_permissions/`) but no skill
documents its usage patterns, async job handling, or cost controls.

**Value:** Textract async jobs (start/get pattern) are error-prone. Guidance
would cover the SNS/SQS notification approach that the project already partially
implements.

**Key topics:**
- Synchronous vs. asynchronous API selection
- `start_document_analysis` / `get_document_analysis` polling pattern
- SNS topic + SQS queue for job completion notifications
- FeatureTypes selection (TABLES, FORMS, QUERIES)
- Per-page cost awareness
- Textract output schema (Blocks, Relationships)

---

### 1.5 `aws/sqs_patterns`
**Gap:** The project uses SQS (`infra/modules/sqs_queue/`) for pipeline
decoupling but has no skill covering dead-letter queues, visibility timeouts,
or Lambda-SQS trigger configuration.

**Value:** Incorrect visibility timeout and missing DLQ are the two most
common causes of duplicate processing and silent message loss in Lambda-SQS
pipelines.

**Key topics:**
- Dead-letter queue configuration
- Visibility timeout sizing relative to Lambda timeout
- Batch size and concurrency limits
- Redrive policy
- FIFO vs. standard queue selection
- SQS as Lambda event source mapping

---

## 2. Frontend (`frontend/`)

### 2.1 `frontend/react_vite_aws`
**Gap:** The frontend (`frontend/`) is a React + Vite SPA that talks to
Lambda-backed APIs and is deployed to AWS (likely S3 + CloudFront based on
`web_portal.tf`). No skill documents the build, deployment, or environment
configuration pattern.

**Value:** The environment variable pattern (`.env.local`, `.env.production`),
the S3 sync command, and CloudFront cache invalidation are repeated steps that
belong in guidance, not tribal knowledge.

**Key topics:**
- Vite `import.meta.env` vs. runtime config
- Build output (`dist/`) to S3 bucket with `aws s3 sync`
- CloudFront distribution + cache invalidation after deploy
- Environment-specific API base URL injection
- Content-Security-Policy headers for API calls

---

### 2.2 `frontend/api_client_patterns`
**Gap:** The project has `frontend/src/api/client.js` but no guidance on
error handling, retry logic, loading states, or authentication headers for
calls to API Gateway.

**Value:** Chat and upload flows (`ChatPage.jsx`, `UploadPage.jsx`) are the
user-facing core of the system. Inconsistent error handling degrades UX and
makes debugging harder.

**Key topics:**
- Centralised axios/fetch wrapper with base URL and auth headers
- Request/response interceptors for error normalisation
- Retry with exponential backoff for transient 5xx
- Abort controller for cancelled requests (navigation away)
- Loading / error / empty state conventions across components

---

### 2.3 `frontend/file_upload_ux`
**Gap:** `UploadPage.jsx` handles invoice file uploads. There is no guidance
on progress indication, file validation, chunked/multipart upload for large
TIF files, or presigned S3 URLs.

**Value:** Invoices can be large multi-page TIF files. Browser upload via API
Gateway has a 10 MB payload limit; presigned S3 URLs bypass this limit and
improve reliability.

**Key topics:**
- Presigned S3 URL pattern (Lambda generates URL, browser uploads directly)
- File type and size validation before upload
- Upload progress bar with XMLHttpRequest or fetch + ReadableStream
- Drag-and-drop with fallback to file input
- Multi-file queue with per-file status

---

## 3. Backend (`src/`)

### 3.1 `python/bedrock_client`
**Gap:** The project uses Bedrock for OCR normalisation and SQL generation
(`src/aws/bedrock_client.py`, `src/analytics/bedrock_sql.py`). No skill
documents Bedrock invocation patterns, prompt engineering, or error handling.

**Value:** Bedrock `invoke_model` error codes (throttling, context length) and
the `converse` API differences from `invoke_model` are non-obvious. Prompt
caching and token budgeting directly affect cost.

**Key topics:**
- `invoke_model` vs. `converse` API selection
- Model ID management (Anthropic Claude on Bedrock, region availability)
- Retry on `ThrottlingException` with jitter
- Prompt structure for extraction tasks (system + user turn)
- Response parsing for structured JSON output
- Token count estimation and context window awareness

---

### 3.2 `python/error_handling_pipeline`
**Gap:** Pipeline stages (`bronze_pipeline.py`, `silver_pipeline.py`,
`gold_model.py`) run in a Step Functions state machine. No skill covers
structured error propagation, retry boundaries, or how to distinguish
recoverable from fatal errors in a multi-stage pipeline.

**Value:** Step Functions retry and catch blocks require errors to be typed
(`States.TaskFailed`, custom error names). Without guidance, all failures look
the same and retries are either too aggressive or absent.

**Key topics:**
- Custom exception hierarchy for pipeline stages
- Raising named errors that Step Functions can catch
- Distinguishing transient (retry) from permanent (DLQ / human review) failures
- Structured error payload with stage, document ID, and cause
- Lambda destination vs. Step Functions error handling

---

### 3.3 `python/logging_structured`
**Gap:** The project has `src/utils/logging.py` and `src/aws/logging_utils.py`
but no skill documents the structured logging contract (fields, levels, context
enrichment) expected across all Lambda handlers and Glue jobs.

**Value:** CloudWatch Insights queries depend on consistent field names.
Without a logged `document_id`, `stage`, and `status` in every log line,
debugging a failed pipeline run requires reading raw text.

**Key topics:**
- JSON log format with mandatory fields (`timestamp`, `level`, `service`,
  `stage`, `document_id`, `correlation_id`)
- Python `logging` + `json_formatter` setup
- Context injection via `logging.LoggerAdapter`
- Log levels and when to use each (DEBUG, INFO, WARNING, ERROR)
- CloudWatch Insights sample queries for the project's log schema

---

### 3.4 `data/athena_patterns`
**Gap:** `src/analytics/athena_client.py` runs Athena queries but no skill
documents query lifecycle management, result pagination, partitioning pruning,
or cost control for Athena.

**Value:** Athena charges per byte scanned. Partition projection and column
pruning can reduce cost by 10-100x. The project already uses Parquet (columnar)
but may not be pruning partitions correctly.

**Key topics:**
- `start_query_execution` / `get_query_execution` polling pattern
- Result pagination with `get_query_results`
- Partition pruning in WHERE clauses for S3 data lake
- Partition projection vs. `MSCK REPAIR TABLE`
- Workgroup configuration (per-query data limit, output location)
- Cost estimation before execution (byte estimate API)

---

### 3.5 `data/ocr_normalisation`
**Gap:** The OCR → LLM normalisation step
(`src/pipeline/ocr.py`, `src/services/ocr_service.py`,
`specs/prompts/bedrock_normalization_prompt.md`) is a core differentiator of
the project but has no formalised guidance on prompt structure, output
validation, or confidence scoring.

**Value:** Normalisation quality is the primary driver of Silver/Gold data
accuracy. Documenting the contract between OCR output and LLM prompt helps
maintain quality as models or prompts evolve.

**Key topics:**
- Prompt template versioning
- Expected output schema and JSON extraction from LLM response
- Confidence threshold for automatic promotion vs. human review routing
- Handling partial extraction (missing fields)
- Regression testing approach for normalisation quality

---

## 4. AWS (cross-cutting)

### 4.1 `aws/bedrock_permissions`
**Gap:** The project has `infra/modules/bedrock_permissions/` but no skill
documents the specific IAM actions required for each Bedrock API call, the
model access request process, or cross-region inference profiles.

**Value:** Bedrock model access must be explicitly requested per region in the
AWS console. Missing this step is the #1 cause of `AccessDeniedException`
on first deploy in a new region.

**Key topics:**
- `bedrock:InvokeModel` vs. `bedrock:InvokeModelWithResponseStream`
- Model access request process (AWS console → Bedrock → Model access)
- Cross-region inference profiles (`us.anthropic.claude-*`)
- Resource-level ARN scoping for Bedrock in IAM policies
- Bedrock Guardrails IAM actions

---

### 4.2 `aws/s3_presigned_urls`
**Gap:** The project uploads invoices via API but no skill documents the
presigned URL pattern for direct browser-to-S3 uploads, which bypasses Lambda
payload limits and improves upload reliability for large files.

**Value:** API Gateway has a hard 10 MB request body limit. TIF invoices can
exceed this. Presigned URLs are the standard solution and the skill would align
frontend and backend guidance.

**Key topics:**
- `generate_presigned_url` for `put_object`
- TTL selection and security considerations
- CORS configuration on the S3 bucket for browser uploads
- Frontend upload flow with presigned URL
- S3 event notification after upload completes

---

### 4.3 `aws/cognito_auth`
**Gap:** The web portal (`SPEC-010-web.md`) serves end users but there is no
guidance on authentication. The current architecture may rely on API keys or
no auth. Cognito User Pools is the standard AWS-native option for this pattern.

**Value:** Adding auth to a deployed system after the fact requires changes to
API Gateway, frontend, and IAM. Documenting the pattern early avoids
retrofitting.

**Key topics:**
- Cognito User Pool + App Client setup in Terraform
- Hosted UI vs. custom login form
- JWT validation in Lambda authoriser
- Frontend auth flow (sign-in, token storage, refresh)
- API Gateway Cognito authoriser configuration

---

### 4.4 `aws/cloudfront_s3_hosting`
**Gap:** The project deploys a React SPA to AWS (inferred from `web_portal.tf`)
but no skill covers the S3 + CloudFront hosting pattern, including cache
invalidation, custom domain, and OAC (Origin Access Control).

**Value:** Without OAC, the S3 bucket must be public. With OAC, the bucket
stays private and CloudFront is the only access point. This is a security
pattern the project should follow.

**Key topics:**
- S3 bucket with public access blocked
- CloudFront OAC (Origin Access Control) replacing legacy OAI
- Cache behavior for `index.html` (no-cache) vs. hashed assets (long TTL)
- Custom error response for SPA routing (403/404 → index.html)
- Cache invalidation after deploy (`create_invalidation`)

---

## Summary Table

| # | Skill slug | Domain | Priority |
|---|-----------|--------|----------|
| 1.1 | `terraform/cost_management` | Infrastructure | High |
| 1.2 | `terraform/environment_promotion` | Infrastructure | Medium |
| 1.3 | `aws/api_gateway` | Infrastructure | High |
| 1.4 | `aws/textract` | Infrastructure | High |
| 1.5 | `aws/sqs_patterns` | Infrastructure | Medium |
| 2.1 | `frontend/react_vite_aws` | Frontend | High |
| 2.2 | `frontend/api_client_patterns` | Frontend | Medium |
| 2.3 | `frontend/file_upload_ux` | Frontend | Medium |
| 3.1 | `python/bedrock_client` | Backend | High |
| 3.2 | `python/error_handling_pipeline` | Backend | High |
| 3.3 | `python/logging_structured` | Backend | Medium |
| 3.4 | `data/athena_patterns` | Backend | Medium |
| 3.5 | `data/ocr_normalisation` | Backend | High |
| 4.1 | `aws/bedrock_permissions` | AWS | High |
| 4.2 | `aws/s3_presigned_urls` | AWS | Medium |
| 4.3 | `aws/cognito_auth` | AWS | Low |
| 4.4 | `aws/cloudfront_s3_hosting` | AWS | Medium |

**17 new skills identified** across 4 domains.

---

## Recommended Implementation Order

**Immediate (close active gaps in deployed system):**
1. `aws/textract` — core pipeline service, no guidance today
2. `aws/api_gateway` — exposes all external APIs
3. `python/bedrock_client` — drives normalisation and analytics
4. `aws/bedrock_permissions` — most common deploy failure
5. `data/ocr_normalisation` — quality of the core output

**Next (improve reliability and maintainability):**
6. `terraform/cost_management` — budget.tf exists but no guidance
7. `python/error_handling_pipeline` — Step Functions error propagation
8. `frontend/react_vite_aws` — SPA deployment pattern
9. `aws/sqs_patterns` — DLQ and visibility timeout correctness

**Later (future MVP2 and scale):**
10. `terraform/environment_promotion` — staging environment
11. `aws/cognito_auth` — user authentication
12. `aws/cloudfront_s3_hosting` — secure static hosting
13. `aws/s3_presigned_urls` — large file uploads
14. `python/logging_structured` — structured log schema
15. `data/athena_patterns` — query cost optimisation
16. `frontend/api_client_patterns` — consistent error handling
17. `frontend/file_upload_ux` — presigned URL upload UX
