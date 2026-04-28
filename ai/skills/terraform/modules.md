# Terraform Module Pattern

## When to use

- Reusable infrastructure components
- Standardized deployments

## Structure

- variables.tf
- main.tf
- outputs.tf

## Best practices

- Avoid hardcoding values
- Use variables for all external inputs
- Keep modules focused (single responsibility)
- Use naming conventions

## Example use cases

- S3 bucket module
- IAM role module
- Glue job module

## Common mistakes

- Over-generalization
- Tight coupling between modules
