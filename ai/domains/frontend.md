# Domain: Frontend (AWS-integrated)

## Purpose

Guidance for building and deploying React SPAs that integrate with AWS backends
(API Gateway, Lambda, S3, CloudFront, Cognito). This domain covers the build
toolchain, AWS deployment pattern, API client design, and file upload UX.

It is distinct from the SaaS frontend domain (`ai/domains/saas.md`), which targets
React apps deployed to Vercel and backed by FastAPI/Supabase rather than AWS services.

---

## Scope

| In scope | Out of scope |
|---|---|
| React + Vite build and environment configuration | SaaS React + Tailwind + Railway/Vercel (see `ai/domains/saas.md`) |
| S3 + CloudFront deploy and cache invalidation | AWS infrastructure declaration (see `ai/domains/terraform.md`) |
| Axios client with API Gateway auth headers | FastAPI backend (see `ai/domains/saas.md`) |
| File upload via S3 presigned URLs | UX design patterns for SaaS (see `ai/domains/saas.md`) |
| Loading / error / empty state conventions | Python Lambda code (see `ai/domains/python.md`) |

---

## Skills

| Skill | File | Description |
|---|---|---|
| React + Vite + AWS deploy | `ai/skills/frontend/react_vite_aws.md` | Vite env variables, S3 sync deploy sequence, CloudFront cache invalidation, CSP headers |
| API client patterns | `ai/skills/frontend/api_client_patterns.md` | Centralised axios client, request/response interceptors, retry logic, abort controller, three-state pattern |
| File upload UX | `ai/skills/frontend/file_upload_ux.md` | Presigned URL upload flow, file validation, XHR progress tracking, drag-and-drop, pipeline status polling |

---

## Policies

No domain-specific policies beyond the global set. See [`ai/policies/global.md`](../policies/global.md).

Key global policies with strong frontend implications:

- **Security By Default** — API keys and tokens must never be committed to source; use Vite env variables (`.env.local`, `.env.production`) and exclude them from git. CSP headers must be configured on the CloudFront distribution.
- **Configuration Over Hardcoding** — API base URLs and feature flags must come from `import.meta.env`, never from inline strings.

---

## References

- Global policies: `ai/policies/global.md`
- Domain index: `ai/domains/index.md`
- Related domains: `ai/domains/aws.md` (CloudFront, S3, API Gateway, Cognito), `ai/domains/saas.md` (alternative SaaS frontend stack)
- Spec that governs domain structure: `specs/rework/SPEC-FW-003.md`
