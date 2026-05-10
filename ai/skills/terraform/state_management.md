# Terraform State Management

Treat state as part of the architecture, not an afterthought.

## Local backend (default for dev/sandbox)

- Use the default local backend for ephemeral environments.
- Do not commit `terraform.tfstate*` files (already in `.gitignore`).
- Re-create state from `terraform apply` rather than restoring backups.

## Remote backend (shared environments)

- Use the S3 backend only when state must be shared across users or CI.
- Bucket: versioning enabled, encryption enabled, `force_destroy = false`.
- Use S3 native locking via `use_lockfile = true` instead of DynamoDB.
  Requires Terraform `>= 1.10` and AWS provider `>= 5.81`.
- Configure via `backend.tf` (gitignored — host-specific). Start from
  `infra/backend.tf.example`.

## Override files

- `override.tf` and `*_override.tf` are gitignored for per-developer
  experimentation without polluting tracked code.
- Never store secrets in overrides; use environment variables or `.tfvars`.

## State hygiene

- Run `terraform state list` before destructive operations.
- Use `terraform state rm` and `terraform import` for surgical fixes
  rather than `taint`/`untaint`.
- Document manual state edits in commit messages or PR descriptions.

## Avoid

- Committing state files or backend credentials.
- Multiple concurrent applies without locking.
- Mixing local and remote state for the same workspace.
