# Domain: Terraform

## Purpose

Guidance for declaring, testing, and maintaining AWS infrastructure as code using
Terraform. This domain covers module design, state management, CI/CD integration,
security, governance, and environment promotion. It is the authoritative source for
how infrastructure is written and managed — not what AWS services do (see `ai/domains/aws.md`).

---

## Scope

| In scope | Out of scope |
|---|---|
| Terraform module design and style | AWS service behaviour and usage patterns (see `ai/domains/aws.md`) |
| State backends and remote state | Python or shell scripts that invoke Terraform |
| IAM least privilege in Terraform | Application code deployed onto the infrastructure |
| Terraform testing (unit, integration, mocks) | Data pipeline logic (see `ai/domains/data-product.md`) |
| CI/CD for Terraform (plan, apply, drift) | SaaS deployment to Railway/Vercel (see `ai/domains/saas.md`) |
| Tagging, budget, and cost governance | |
| Environment promotion (dev → staging → prod) | |
| Resource import (manual and discovery) | |
| Security and observability outputs | |

---

## Skills

| Skill | File | Description |
|---|---|---|
| Style conventions | `ai/skills/terraform/terraform_style.md` | Terraform code structure and style conventions |
| Modules | `ai/skills/terraform/modules.md` | Reusable module patterns |
| State management | `ai/skills/terraform/state_management.md` | State backends, overrides, and hygiene |
| IAM least privilege | `ai/skills/terraform/iam_least_privilege.md` | IAM policies with least privilege principle |
| Testing | `ai/skills/terraform/terraform_testing.md` | Testing patterns (unit, integration, assertions) |
| Mocks | `ai/skills/terraform/terraform_mocks.md` | Mock providers for testing without AWS |
| CI/CD | `ai/skills/terraform/terraform_ci_cd.md` | CI/CD patterns for validation and testing |
| Refactoring | `ai/skills/terraform/terraform_refactoring.md` | Refactor Terraform into reusable modules |
| Stacks | `ai/skills/terraform/terraform_stacks.md` | Multi-environment infrastructure with Terraform Stacks |
| Orchestration | `ai/skills/terraform/terraform_orchestration.md` | Orchestrate execution using CI/CD and external tools |
| Import (manual) | `ai/skills/terraform/terraform_import_manual.md` | Import existing resources manually |
| Import (discovery) | `ai/skills/terraform/terraform_import_discovery.md` | Discover and bulk import resources |
| Security | `ai/skills/terraform/terraform_security.md` | Security best practices for infrastructure |
| Observability | `ai/skills/terraform/terraform_observability.md` | CloudWatch log groups, retention policies, mandatory outputs |
| Governance | `ai/skills/terraform/terraform_governance.md` | Tagging enforcement, budget governance, cost awareness, drift management |
| Environment promotion | `ai/skills/terraform/environment_promotion.md` | Directory-per-environment pattern, state isolation, immutable artifact promotion |

---

## Policies

No domain-specific policies beyond the global set. See [`ai/policies/global.md`](../policies/global.md).

Key constraints from `AGENTS.md` that are enforced at the Terraform level:

- `terraform apply` and `terraform destroy` require explicit user approval — never run autonomously.
- IAM changes require explicit review before applying.
- S3 versioning must not be enabled by default — only when explicitly requested and justified.
- Every resource must carry `local.common_tags` including `CostCenter`.
- Every module must expose `log_group_name`, `log_group_arn`, and `resource_arn` as outputs.
- `terraform.tfstate` must never be deleted or overwritten.

Preferred execution:

- Use `make <target>` when available.
- On Windows, use `scripts/windows/run_make.ps1` or the documented wrapper.
- Run Terraform commands directly from `infra/` — never introduce hidden automation.

---

## References

- Global policies: `ai/policies/global.md`
- Domain index: `ai/domains/index.md`
- Related domains: `ai/domains/aws.md`
- Agent operational policies: `AGENTS.md` (Approval Boundaries and SPEC-009 sections)
- Spec that governs domain structure: `specs/rework/SPEC-FW-003.md`
