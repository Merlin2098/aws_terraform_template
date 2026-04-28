# Terraform CI/CD Pattern

## When to use

- Automating validation of Terraform code
- Enforcing quality in pull requests
- Running tests in pipelines

## Pipeline stages

1. Format check (terraform fmt)
2. Validate (terraform validate)
3. Unit tests (plan mode)
4. Integration tests (apply mode, optional)

## Recommended strategy

- Run unit tests on every PR
- Run integration tests on merge to main
- Separate test types using filters

## GitHub Actions pattern

- Setup Terraform
- Run fmt and validate
- Run terraform test

## Best practices

- Use mocks for unit tests (no credentials)
- Store AWS credentials as secrets
- Avoid running apply in PR pipelines
- Keep pipelines fast

## Execution model

- CI runs validation only
- Deployment requires manual approval

## Avoid

- Running integration tests on every commit
- Hardcoding credentials
- Mixing validation and deployment
