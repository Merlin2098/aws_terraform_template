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

Use the decision tree below (R1 wins over R2, R2 over R3, etc.). Stop at the first rule that fires.

| Rule | Condition | Mode |
|------|-----------|------|
| R1 | Needs OS library or custom runtime | **ECR** |
| R2 | Any native binary lacks a `manylinux`/`abi3` wheel for `linux/amd64` | **ECR** |
| R3 | Artifact ≥ 250 MB unzipped | **ECR** |
| R4 | Build > 5 min recurrently | **ECR** |
| R5 | Heavy dependency block shared by ≥ 3 Lambdas | **ZIP + Layer** |
| R6 | None of the above | **ZIP** |

**Glue-first check:** if the function uses `awswrangler + pandas + pyarrow` for batch work, prefer Glue before applying the tree.

**`boto3` rule:** exclude from ZIP/Layer (runtime provides it). Include in ECR (base image version is not guaranteed).

**Native binaries cross-cutting rule:** any artifact with native binaries must be built on Linux — via `public.ecr.aws/sam/build-python3.x` or `pip install --platform manylinux2014_x86_64 --only-binary=:all: --target`. The Windows host never produces the final artifact for native dependencies.

See [`ai/skills/aws/lambda_packaging.md`](lambda_packaging.md) for full ECR patterns, Dockerfile, and build script.
See [`docs/adr/0002-lambda-packaging-strategy.md`](../../../docs/adr/0002-lambda-packaging-strategy.md) for the rationale.

## Avoid

- Large workloads (use Glue instead)
- Long-running tasks
- ZIP deployment when `pyarrow` is a dependency (R3 fires: ~175 MB unzipped, exceeds 250 MB limit)
- Hardcoding `latest` as `image_uri` tag — Terraform cannot detect updates
