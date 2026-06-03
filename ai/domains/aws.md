# Domain: AWS

## Purpose

Guidance for using AWS managed services correctly and securely. This domain covers
service-specific patterns, IAM configuration, observability, and smoke testing.
It does not cover how to declare those services in Terraform — that belongs in
`ai/domains/terraform.md`.

---

## Scope

| In scope | Out of scope |
|---|---|
| Service-specific usage patterns (Lambda, S3, SQS, etc.) | Terraform resource declarations (see `ai/domains/terraform.md`) |
| IAM role and policy design | Python job code running on AWS (see `ai/domains/python.md`) |
| CloudWatch logging and observability | SaaS auth via Supabase (see `ai/domains/saas.md`) |
| Smoke testing and resource validation | Data pipeline logic (see `ai/domains/data-product.md`) |
| API Gateway, CloudFront, Cognito patterns | React frontend code (see `ai/domains/frontend.md`) |
| Bedrock model access and invocation | |
| Textract async workflows | |

---

## Skills

| Skill | File | Description |
|---|---|---|
| Lambda functions | `ai/skills/aws/lambda_functions.md` | Event-driven compute with AWS Lambda |
| S3 data lake | `ai/skills/aws/s3_data_lake.md` | Data lake architecture using S3 |
| S3 presigned URLs | `ai/skills/aws/s3_presigned_urls.md` | Presigned PUT/POST URL generation, TTL selection, CORS, and S3 event trigger |
| SQS patterns | `ai/skills/aws/sqs_patterns.md` | Visibility timeout, dead-letter queues, batch configuration, Lambda event source mapping |
| Step Functions | `ai/skills/aws/step_functions.md` | Workflow orchestration using Step Functions |
| EventBridge | `ai/skills/aws/eventbridge.md` | Event-driven architecture using EventBridge |
| API Gateway | `ai/skills/aws/api_gateway.md` | HTTP API vs REST API, Lambda proxy integration, CORS, throttling, Cognito authoriser |
| CloudFront + S3 hosting | `ai/skills/aws/cloudfront_s3_hosting.md` | Static hosting with OAC, cache behavior split, SPA routing, cache invalidation |
| CloudWatch logging | `ai/skills/aws/cloudwatch_logging.md` | Logging and monitoring with CloudWatch |
| Glue jobs | `ai/skills/aws/glue_jobs.md` | AWS Glue job design patterns |
| Textract | `ai/skills/aws/textract.md` | Async Textract workflows, SNS/SQS notification pattern, FeatureTypes cost guidance |
| Bedrock permissions | `ai/skills/aws/bedrock_permissions.md` | IAM actions, model access activation, cross-region inference ARNs |
| Cognito auth | `ai/skills/aws/cognito_auth.md` | User Pool setup, JWT validation, API Gateway authoriser, frontend auth token flow |
| IAM policies | `ai/skills/aws/iam_policies.md` | IAM roles and least privilege policies |
| Smoke testing | `ai/skills/aws/aws_smoke_testing.md` | Smoke test and validation scripts — generates `tests/aws/` in host repositories |

---

## Policies

No domain-specific policies beyond the global set. See [`ai/policies/global.md`](../policies/global.md).

Key global policies with strong AWS implications:

- **Security By Default** — all S3 buckets block public access; IAM roles use least privilege; no wildcard resource ARNs in production.
- **Configuration Over Hardcoding** — ARNs, bucket names, and queue URLs come from Terraform outputs or environment variables, never hardcoded.

Additional constraints from `AGENTS.md` (SPEC-009):

- Every service that produces logs must have an explicit `aws_cloudwatch_log_group` with `retention_in_days` set.
- Every environment must include `aws_budgets_budget`.
- `local.common_tags` (including `CostCenter`) must be applied to every resource.

---

## References

- Global policies: `ai/policies/global.md`
- Domain index: `ai/domains/index.md`
- Related domains: `ai/domains/terraform.md`, `ai/domains/python.md`, `ai/domains/data-product.md`
- Agent operational policies: `AGENTS.md` (SPEC-009 section)
- Spec that governs domain structure: `specs/rework/SPEC-FW-003.md`
