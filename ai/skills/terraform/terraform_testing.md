# Terraform Testing Pattern

## When to use

- Validating Terraform modules
- Preventing breaking changes
- Ensuring infrastructure correctness

## Test types

- Unit tests → plan mode (fast, no infra)
- Integration tests → apply mode (real AWS resources)
- Mock tests → simulated provider behavior

## Structure

- tests/*.tftest.hcl files
- run blocks define test scenarios
- assert blocks validate conditions

## Best practices

- Default to plan mode
- Use integration tests only when needed
- Test outputs and resource attributes
- Cover multiple variable combinations

## Common patterns

- Validate outputs (IDs, formats)
- Test conditional resources (count, for_each)
- Validate tags and configurations
- Use expect_failures for negative tests

## Avoid

- Running apply tests on every change
- Mixing unit and integration tests
- Skipping validation logic
