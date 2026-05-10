# Infra baseline

## Context

This spec captures the invariants of [`infra/`](../../infra/) as shipped
by the template. It defines the resources, tags, and security defaults
that any host repo inherits before adding its own infrastructure.

## Contract

### Resources always present

| Resource | File | Purpose |
|---|---|---|
| `aws_s3_bucket.artifacts` | [`infra/main.tf:18`](../../infra/main.tf#L18) | Stores packaged runtime artifacts (`make package` output). |
| `aws_s3_bucket_versioning.artifacts` | [`infra/main.tf:24`](../../infra/main.tf#L24) | Versioning toggled by `enable_artifact_bucket_versioning` (default off in dev). |
| `aws_s3_bucket_server_side_encryption_configuration.artifacts` | [`infra/main.tf:32`](../../infra/main.tf#L32) | AES256 encryption at rest. |
| `aws_s3_bucket_public_access_block.artifacts` | [`infra/main.tf:42`](../../infra/main.tf#L42) | All four public-access blocks set to `true`. |
| `aws_s3_object.artifact_bundle` | [`infra/main.tf:51`](../../infra/main.tf#L51) | The packaged artifact uploaded by the host pipeline. |
| `aws_iam_role.data_job_execution` | [`infra/main.tf:70`](../../infra/main.tf#L70) | Glue (and similar batch jobs) execution role. |
| `aws_iam_role_policy_attachment.glue_service_role` | [`infra/main.tf:76`](../../infra/main.tf#L76) | Attaches `AWSGlueServiceRole` managed policy. |
| `aws_iam_role_policy.artifact_access` | [`infra/main.tf:97`](../../infra/main.tf#L97) | Scoped read/write/list on the artifact bucket only. |

### Standard tags

Applied to every Terraform-managed resource via `local.common_tags`
([`infra/main.tf:7-15`](../../infra/main.tf#L7-L15)):

- `Project` — from `var.project_name`
- `Environment` — from `var.environment`
- `Owner` — from `var.owner`
- `ManagedBy` — hardcoded to `"Terraform"`

Additional tags merge from `var.tags`.

### Variables exposed

Defined in [`infra/variables.tf`](../../infra/variables.tf): `project_name`,
`environment`, `owner`, `aws_region`, `artifact_path`,
`artifact_bucket_suffix`, `artifact_bucket_force_destroy`,
`enable_artifact_bucket_versioning`, `execution_role_name`, `tags`.

### Security defaults

- Public access blocked at the bucket level (all four flags `true`).
- Server-side encryption enabled (AES256). KMS is not used by default to
  keep dev sandboxes cheap and easy to destroy.
- IAM role uses an inline policy scoped to a single bucket ARN; no
  wildcards on `Resource`.

### Dev-friendly defaults

- `artifact_bucket_force_destroy = true` so `terraform destroy` works
  cleanly in dev/sandbox.
- `enable_artifact_bucket_versioning = false` to avoid accumulating object
  versions in dev.

## Invariants

- Standard tags must remain applied to every new resource added to
  `infra/`. Use `local.common_tags` (merge with resource-specific tags if
  needed); do not bypass.
- The S3 public-access block must remain enabled on every bucket the
  template owns.
- Encryption at rest must remain enabled on every bucket the template owns.
- IAM policies must remain scoped: no `Resource = "*"` on data buckets.
- The baseline must remain `terraform apply → destroy → apply` clean,
  per [`docs/terra_principles.md`](../../docs/terra_principles.md).

## Out of scope

- Production-grade hardening (KMS keys, VPC endpoints, CloudTrail data
  events). Hosts add these as needed.
- Multi-region or multi-account topology.
- Remote backend configuration. See
  [`infra/backend.tf.example`](../../infra/backend.tf.example) and the
  `state_management` skill.

## References

- [`infra/main.tf`](../../infra/main.tf), [`infra/variables.tf`](../../infra/variables.tf), [`infra/outputs.tf`](../../infra/outputs.tf)
- [`docs/terra_principles.md`](../../docs/terra_principles.md)
- [`ai/skills/terraform/state_management.md`](../../ai/skills/terraform/state_management.md)
- [`ai/skills/terraform/iam_least_privilege.md`](../../ai/skills/terraform/iam_least_privilege.md)
