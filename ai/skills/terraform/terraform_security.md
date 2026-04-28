# Terraform Security Pattern

## When to use

- Writing Terraform code for production
- Handling sensitive data
- Securing AWS resources

## Core principles

- Encrypt everything at rest
- Use private networking by default
- Apply least privilege access
- Never store secrets in state

## Secrets management (priority order)

1. Use native secrets manager (AWS Secrets Manager, etc.)
2. Use ephemeral resources for sensitive data
3. Only as last resort, use regular resources

## Sensitive data rules

- Mark outputs as `sensitive = true`
- Avoid hardcoded credentials
- Use variables for secrets
- Prefer identity-based auth (OIDC)

## Infrastructure hardening

- Enable encryption (KMS where possible)
- Block public access (e.g., S3)
- Enable logging and monitoring
- Use versioning for storage

## Example patterns

- S3: encryption + public access block
- RDS: managed passwords
- IAM: scoped permissions

## Avoid

- Storing secrets in Terraform state
- Hardcoding credentials
- Public access by default
- Over-permissioned IAM policies
