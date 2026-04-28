# IAM Policy Pattern

## When to use

- Defining permissions for AWS resources
- Securing infrastructure

## Core idea

Grant minimum permissions required.

## Best practices

- Use least privilege
- Scope resources (ARNs)
- Avoid "*"
- Separate roles by service

## Patterns

- Lambda execution role
- Glue job role
- S3 access policies

## Avoid

- Over-permissioned roles
- Shared roles across services
