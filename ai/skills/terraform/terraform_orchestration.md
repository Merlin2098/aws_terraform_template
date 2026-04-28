# Terraform Orchestration Pattern

## When to use

- Coordinating infrastructure changes
- Managing lifecycle workflows
- Integrating Terraform with pipelines

## Core idea

Keep Terraform declarative, and handle orchestration externally (CI/CD, scripts).

## Approaches

- CI/CD pipelines (GitHub Actions)
- Makefile commands
- Step Functions (for AWS workflows)

## Patterns

- Validate → Plan → Apply
- Separate validation from deployment
- Manual approval for production

## Best practices

- Never auto-apply in CI
- Use plan mode for validation
- Keep execution explicit (make deploy)

## Advanced concepts

- Trigger actions after infrastructure changes
- Use external systems for lifecycle events
- Avoid embedding imperative logic in Terraform

## Avoid

- Mixing orchestration with infrastructure code
- Hidden execution flows
- Auto-triggered destructive actions
