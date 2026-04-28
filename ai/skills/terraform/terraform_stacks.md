# Terraform Stacks Pattern

## When to use

- Managing multi-environment infrastructure (dev, prod)
- Multi-region deployments
- Large-scale infrastructure orchestration

## Core concepts

- Stack → full system
- Component → module wrapper
- Deployment → environment instance

## Structure

- .tfcomponent.hcl → components
- .tfdeploy.hcl → deployments

## Key ideas

- Components reference modules
- Deployments define environments
- Providers configured at stack level

## Best practices

- Use stacks for orchestration, not logic
- Keep modules reusable and independent
- Use variables for environment differences
- Use identity-based authentication (OIDC)

## Common use cases

- Multi-region AWS deployments
- Dev / staging / prod environments
- Cross-account infrastructure

## Avoid

- Embedding business logic in stacks
- Overcomplicating component structure
- Using stacks for small projects
