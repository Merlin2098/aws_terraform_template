# Terraform Manual Import Pattern

## When to use

- Resource not supported by Terraform Search
- Legacy infrastructure
- Partial provider support

## Core idea

Manually define resources and import them into Terraform state.

## Workflow

1. Discover resources using CLI (aws, gcloud, etc.)
2. Create resource blocks in Terraform
3. Add import blocks
4. Run plan and apply

## Example

- aws rds describe-db-instances
- aws dynamodb list-tables

## Best practices

- Start with minimal resource config
- Add attributes incrementally
- Validate with `terraform plan`
- Use consistent naming

## Bulk import

- Script resource discovery
- Generate resource + import blocks
- Review before apply

## Avoid

- Importing without understanding resource config
- Copying full provider output blindly
- Skipping plan validation
