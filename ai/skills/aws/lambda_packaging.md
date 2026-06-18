# Lambda Packaging — ECR Container Image

## When to use

When the packaging decision tree in [`lambda_functions.md`](lambda_functions.md) fires R1–R4.
Most commonly: any function that imports `pyarrow` (R3 — ~175 MB unzipped alone, exceeds the 250 MB hard limit).

---

## Dockerfile

Place the Dockerfile at `docker/Dockerfile` in the project root. Use the AWS-provided Lambda Python base image. It includes the Lambda Runtime Interface Client required for Lambda to invoke the handler.

```dockerfile
FROM public.ecr.aws/lambda/python:3.12
COPY src/requirements-lambda.txt .
RUN pip install -r requirements-lambda.txt --no-cache-dir
COPY src/ ${LAMBDA_TASK_ROOT}/src/
CMD ["src.jobs.handler.handler"]
```

**Rules:**
- Always place the Dockerfile at `docker/Dockerfile` — never in the project root or next to application code.
- Use `public.ecr.aws/lambda/python:3.12` (or the target version) — not `python:3.12-slim`. The Lambda base image ships the RIC; generic images do not.
- `CMD` is the dotted module path to the handler function, not a shell command.
- Keep `requirements-lambda.txt` minimal — only packages the handler directly imports. Do not copy from `pyproject.toml` dev/cloud extras.

---

## requirements-lambda.txt

Declare only direct runtime imports. Include `boto3` (ECR mode — base image version not guaranteed).

```
boto3
pyarrow
```

---

## Build and push script (`scripts/docker_push.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG=$(git rev-parse --short HEAD)
REPO_URL=$(terraform -chdir=infra output -raw ecr_repository_url)
REGION="${AWS_REGION:-us-east-1}"

docker build \
  --platform linux/amd64 \
  --provenance=false \
  --file docker/Dockerfile \
  -t "$REPO_URL:$IMAGE_TAG" \
  -t "$REPO_URL:latest" \
  .

aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "$REPO_URL"

docker push "$REPO_URL:$IMAGE_TAG"
docker push "$REPO_URL:latest"

echo "Pushed $REPO_URL:$IMAGE_TAG"
```

### `--provenance=false` is mandatory

Docker Desktop on Windows (and any BuildKit ≥ 0.11) generates an **OCI manifest list** with an embedded attestation manifest by default. Lambda rejects this format:

```
InvalidParameterValueException: The image manifest, config or layer media type
for the source image ... is not supported.
```

`--provenance=false` produces a **single-platform Docker schema v2 manifest** — the only format Lambda accepts. Omitting this flag causes `terraform apply` to fail even though the ECR push succeeds.

### `--platform linux/amd64` is mandatory

Lambda runs on `linux/amd64`. Building without this flag on an ARM host (Apple Silicon, etc.) produces an image Lambda cannot execute.

---

## Terraform — ECR repository

```hcl
# infra/ecr/main.tf
resource "aws_ecr_repository" "lambda_image" {
  name         = "${var.project}-${var.environment}-${var.service_name}"
  force_delete = true   # required: terraform destroy fails if images remain
  tags         = var.tags
}

resource "aws_ecr_lifecycle_policy" "lambda_image" {
  repository = aws_ecr_repository.lambda_image.name
  policy = jsonencode({ rules = [{
    rulePriority = 1
    description  = "Keep last 5 images"
    selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 5 }
    action       = { type = "expire" }
  }]})
}

output "repository_url" {
  value = aws_ecr_repository.lambda_image.repository_url
}
```

---

## Terraform — Lambda function (image-based)

```hcl
resource "aws_lambda_function" "handler" {
  function_name = "${var.project}-${var.environment}-${var.service_name}"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}:${var.image_tag}"
  role          = var.execution_role_arn

  timeout      = 300
  memory_size  = 512

  environment {
    variables = var.env_vars
  }
}
```

**Rules:**
- `package_type = "Image"` — required.
- `image_uri` must reference a specific tag, not `latest`, so Terraform detects image updates.
- `filename`, `s3_key`, `s3_object_version`, and `source_code_hash` must be **absent** — including them causes a provider error with image-based functions.
- `force_delete = true` on the ECR repository — `terraform destroy` fails if images remain.

---

## Deployment order

1. `terraform apply` — provision ECR repository (first time only).
2. `bash scripts/docker_push.sh` — build and push image, note the `IMAGE_TAG` printed.
3. `terraform apply -var image_tag=<IMAGE_TAG>` — update the Lambda function to the new image.

Run step 2 before step 3 on every handler or dependency change.

---

## Known pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `InvalidParameterValueException: image manifest ... not supported` | OCI manifest list from BuildKit | Add `--provenance=false` to `docker build` |
| `terraform apply` detects no change after new image push | `image_uri` hardcoded to `latest` | Pass SHA tag via `var.image_tag` |
| `terraform destroy` fails: repository not empty | `force_delete` missing | Set `force_delete = true` on `aws_ecr_repository` |
| `InvalidParameterValueException: Unzipped size must be smaller than 262144000 bytes` | ZIP deployment with `pyarrow` | Switch to ECR (R3 fires) |
| Import errors at Lambda runtime | Native wheels built on Windows | Build image via Docker with `--platform linux/amd64` |
