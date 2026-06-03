# Domain: Python

## Purpose

Guidance for writing maintainable Python code in the context of data pipelines,
AWS Lambda handlers, and Glue jobs. This domain covers project structure, testing,
error handling, structured logging, and AWS SDK client patterns. It focuses on
code quality and correctness — not on the AWS services the code runs on
(see `ai/domains/aws.md`) or the data contracts it must satisfy (see `ai/domains/data-product.md`).

---

## Scope

| In scope | Out of scope |
|---|---|
| Python project structure and packaging | FastAPI / SaaS backend (see `ai/domains/saas.md`) |
| Testing patterns for pipelines and AWS boundaries | Terraform or infrastructure code |
| Typed exception hierarchies for Step Functions | SQL transformation logic (see `ai/domains/data-product.md`) |
| Structured JSON logging and CloudWatch Insights | AWS service configuration (see `ai/domains/aws.md`) |
| Bedrock SDK invocation patterns | Frontend JavaScript / TypeScript |
| Error handling and retry logic | |

---

## Skills

| Skill | File | Description |
|---|---|---|
| Project guidance | `ai/skills/python/python_project_guidance.md` | Simple, maintainable Python automation and pipeline code |
| Testing quality | `ai/skills/python/python_testing_quality.md` | Testing guidance for Python automation, data workflows, and AWS boundaries |
| Bedrock client | `ai/skills/python/bedrock_client.md` | `invoke_model` and `converse` patterns, throttling retry, response parsing, context window guard |
| Error handling (pipeline) | `ai/skills/python/error_handling_pipeline.md` | Typed exception hierarchy, Step Functions Catch integration, structured error payloads |
| Structured logging | `ai/skills/python/logging_structured.md` | Mandatory log field contract, JSON formatter, LoggerAdapter context injection, CloudWatch Insights queries |

---

## Policies

No domain-specific policies beyond the global set. See [`ai/policies/global.md`](../policies/global.md).

Key global policies with strong Python implications:

- **Configuration Over Hardcoding** — S3 paths, model IDs, thresholds, and queue URLs must come from environment variables or config files, never from inline literals.
- **Security By Default** — AWS credentials must never appear in code; use IAM roles attached to the execution environment.

Package manager awareness (from `AGENTS.md`):

- Inspect the repository before choosing a dependency workflow.
- Follow `requirements*.txt` workflows when the host uses `pip`.
- Follow `pyproject.toml` + `uv.lock` workflows when the host uses `uv`.

---

## References

- Global policies: `ai/policies/global.md`
- Domain index: `ai/domains/index.md`
- Related domains: `ai/domains/aws.md`, `ai/domains/data-product.md`
- Spec that governs domain structure: `specs/rework/SPEC-FW-003.md`
