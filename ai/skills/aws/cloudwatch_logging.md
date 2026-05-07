# CloudWatch Logging Pattern

## When to use

- Monitoring AWS services
- Debugging pipelines

## Core idea

Centralize logs and metrics.

## Patterns

- Structured logs
- Metrics and alarms
- Log groups per service

## Best practices

- Log meaningful events
- Explicitly declare log groups in Terraform instead of relying on
  service-created defaults
- Set retention policies
- Use short retention windows for dev and sandbox environments unless a longer
  period is explicitly required
- Monitor errors and latency

## Common use cases

- Lambda logs
- Glue job logs
- Step Functions execution logs

## Avoid

- Ignoring logs
- Infinite retention
- Unmanaged or auto-created log groups that are not owned by Terraform
