# Terraform Style Pattern

## When to use

- Writing or refactoring Terraform code
- Standardizing infrastructure
- Reviewing Terraform configurations

## File structure

- terraform.tf → versions
- providers.tf → providers
- main.tf → resources
- variables.tf → inputs
- outputs.tf → outputs
- locals.tf → shared values

## Naming conventions

- lowercase with underscores
- descriptive names
- singular resources
- use "main" when only one exists

## Code structure

1. Meta-arguments (count, for_each)
2. Arguments
3. Nested blocks
4. Lifecycle (last)

## Best practices

- Use variables for all configurable values
- Add descriptions to all variables and outputs
- Use type constraints (string, object, list)
- Use validation blocks

## Resource patterns

- Prefer `for_each` over `count`
- Use locals for repeated values
- Avoid hardcoding values

## Formatting

- 2 spaces indentation
- consistent alignment
- run `terraform fmt`

## Validation

- terraform validate
- lint tools (tflint, checkov)

## Avoid

- mixing logic across files
- hardcoded values
- inconsistent naming
- skipping validation
