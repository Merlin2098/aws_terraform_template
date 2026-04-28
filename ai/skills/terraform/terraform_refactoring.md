# Terraform Refactoring Pattern

## When to use

- Converting monolithic Terraform into modules
- Improving maintainability and reuse
- Standardizing infrastructure

## Core idea

Break large Terraform configurations into small, reusable modules with clear interfaces.

## Steps

1. Identify logical groupings (network, compute, data)
2. Extract into modules
3. Define inputs (variables) and outputs
4. Replace hardcoded values with variables

## Module structure

- main.tf
- variables.tf
- outputs.tf

## Best practices

- One responsibility per module
- Use typed variables (object, list, map)
- Add validations for inputs
- Avoid over-abstraction

## Refactoring patterns

- Group related resources (VPC + subnets)
- Replace repetition with for_each
- Use modules instead of duplicated resources

## State migration

- Use `moved` blocks (Terraform ≥1.1)
- Or `terraform state mv`

## Avoid

- Overly generic modules
- Tight coupling between modules
- Breaking state without migration
