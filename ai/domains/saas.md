# Domain: SaaS

## Purpose

Guidance for building modern SaaS applications using React, FastAPI, and Supabase.
This domain is independent of the existing Data Product, AWS, Terraform, and Python domains.

---

## Scope

| In scope | Out of scope |
|---|---|
| React + Vite + Tailwind frontend | AWS-specific infra (see `domains/aws`) |
| FastAPI backend with service/repository layers | AWS Lambda Python (see `ai/skills/python/`) |
| PostgreSQL / Supabase database | Data lake / ETL pipelines |
| Supabase Auth + RBAC | Cognito auth (see `ai/skills/aws/cognito_auth.md`) |
| Operational SaaS analytics (KPIs) | Data warehouse analytics (see `ai/skills/data/`) |
| Railway / Vercel deployment | AWS CloudFront / S3 deploy (see `ai/skills/frontend/`) |
| SaaS UX patterns | Design system tokens / brand |

---

## Skills

| Skill Group | File | Key technologies |
|---|---|---|
| SG1 — Frontend | `ai/skills/saas/frontend.md` | React, Vite, Tailwind, React Router, Axios |
| SG2 — Backend | `ai/skills/saas/backend.md` | FastAPI, SQLAlchemy, Alembic, Pydantic |
| SG3 — Database | `ai/skills/saas/database.md` | PostgreSQL, Supabase, migrations, soft delete |
| SG4 — Authentication | `ai/skills/saas/auth.md` | Supabase Auth, JWT, RBAC |
| SG5 — SaaS Analytics | `ai/skills/saas/analytics.md` | KPIs, dashboards, business metrics |
| SG6 — Deployment | `ai/skills/saas/deployment.md` | Railway, Vercel, GitHub Actions, env config |
| SG7 — UX/UI | `ai/skills/saas/ux.md` | Dashboard design, form flows, accessibility |

---

## Domain Policies

These policies apply within the SaaS domain in addition to the global policies in
[`ai/policies/global.md`](../policies/global.md).

### Frontend
- **Component First** — design reusable components before pages
- **No Business Logic Inside UI Components** — business logic belongs in hooks or services
- **API Driven UI** — all data comes from the API; no direct database access from the frontend

### Backend
- **Controller → Service → Repository** — strict layering; no layer skips
- **Business Logic Only In Services** — routers and repositories contain no business rules
- **Database Access Only Through Repositories** — no raw DB calls outside the repository layer

### Database
- **Soft Delete By Default** — use `deleted_at` timestamp; never hard-delete user data
- **Audit Fields Mandatory** — all tables include `created_at`, `updated_at`, `created_by`
- **No Direct Production Changes** — all schema changes through Alembic migrations

### Authentication
- **Authentication Managed By Supabase** — do not build custom auth
- **Authorization Managed By Application Layer** — RBAC logic lives in the service layer, not in Supabase RLS alone

### Analytics
- **Analytics Requirements Must Be Defined During Data Modeling** — add metrics columns at schema design time
- **Historical Tracking Required** — aggregate metrics must be snapshotted, not computed from live data only

### Deployment
- **No Secrets In Source Code** — all secrets via environment variables or secret manager
- **Environment Specific Configuration** — separate `.env` files per environment; never share prod config with dev
- **Deploy Must Be Reproducible** — any team member can reproduce the deploy from the documented steps

### UX
- **Most Frequent Operations In Less Than 3 Clicks** — measure click depth for top-5 user actions
- **Minimize User Friction** — prefer smart defaults, inline validation, and progressive disclosure

---

## Standard RBAC Roles

| Role | Description |
|---|---|
| `OWNER` | Full access; can manage users and billing |
| `ADMIN` | Operational admin; cannot manage billing |
| `SALES` | Create and manage leads and appointments |
| `SPECIALIST` | Read and update assigned records |

---

## Future Capabilities (not yet implemented)

Prepare the structure but do not implement until explicitly requested:

- Multi-Tenant architecture
- Subscription Billing
- Payments integration
- Notifications (email, push)
- WhatsApp integration
- CRM features
- Customer Portal

When any of these is activated, create a dedicated spec and skill file before implementing.

---

## References

- Skills: `ai/skills/saas/`
- Global policies: `ai/policies/global.md`
- Domain index: `ai/domains/index.md`
- Spec that defined this domain: `specs/rework/SPEC-FW-002.md`
