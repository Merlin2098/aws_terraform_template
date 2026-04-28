# Terraform Mock Provider Pattern

## When to use

- Fast unit testing without AWS credentials
- Validating Terraform logic locally
- CI pipelines without cloud access

## Concept

Mock providers simulate AWS resources during `plan` execution.

## Key elements

- mock_provider
- mock_resource
- mock_data

## Example use cases

- Simulate EC2 instance creation
- Mock AMI data sources
- Test subnet/VPC relationships

## Best practices

- Use plan mode only (mocks do not work with apply)
- Define realistic default values
- Keep mocks simple and predictable
- Use mocks for logic, not real behavior

## Benefits

- Fast execution
- No AWS costs
- No credentials required

## Limitations

- No real infrastructure validation
- Must be manually updated if schema changes
- Cannot test real dependencies

## Avoid

- Using mocks for integration tests
- Overcomplicating mock definitions
