# AWS Lambda Pattern

## When to use

- Event-driven processing
- Lightweight transformations
- API integrations

## Core idea

Run small, stateless functions triggered by events.

## Common triggers

- API Gateway
- S3 events
- EventBridge
- SQS

## Best practices

- Keep functions small and focused
- Use environment variables for config
- Handle retries and idempotency
- Log to CloudWatch

## Packaging

- Zip artifact
- Dependencies included
- Use layers if needed

## Avoid

- Large workloads (use Glue instead)
- Long-running tasks
