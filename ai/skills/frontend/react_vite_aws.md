# React + Vite + AWS Deployment Pattern

## When to use

- Building or deploying the React + Vite SPA in this project
- Adding environment-specific configuration for dev, staging, or production
- Writing or reviewing the frontend build and deploy pipeline

## Core idea

Vite embeds environment variables at build time. There is no server-side
injection. The API base URL, Cognito pool ID, and AWS region must all be set
before `npm run build` runs — not at runtime. Read all infrastructure values
from `terraform output` before building.

---

## Environment variables

Vite exposes only variables prefixed with `VITE_` to browser code via
`import.meta.env`. Variables without this prefix are not included in the bundle.

Standard variable names for this project:

```
VITE_API_BASE_URL=https://abc123.execute-api.us-east-1.amazonaws.com
VITE_AWS_REGION=us-east-1
VITE_USER_POOL_ID=us-east-1_XxXxXx
VITE_USER_POOL_CLIENT_ID=abc123clientid
```

For local development, store these in `.env.local` (gitignored). For CI/CD
builds, inject them as environment variables before running `npm run build`.

Never hardcode infrastructure URLs in source files — they change per environment
and per deploy.

---

## Reading values from Terraform output

Before building, populate `.env.production` (or inject as CI env vars) by
reading from `terraform output`:

```powershell
# scripts/build_frontend.ps1
$api_url      = terraform -chdir=infra output -raw api_endpoint
$region       = terraform -chdir=infra output -raw aws_region
$pool_id      = terraform -chdir=infra output -raw user_pool_id
$client_id    = terraform -chdir=infra output -raw user_pool_client_id

$env_content = @"
VITE_API_BASE_URL=$api_url
VITE_AWS_REGION=$region
VITE_USER_POOL_ID=$pool_id
VITE_USER_POOL_CLIENT_ID=$client_id
"@

$env_content | Out-File -FilePath frontend/.env.production -Encoding utf8
cd frontend && npm run build
```

---

## Build and deploy sequence

```powershell
# 1. Read infra outputs
$bucket  = terraform -chdir=infra output -raw frontend_bucket_name
$dist_id = terraform -chdir=infra output -raw cloudfront_distribution_id

# 2. Build
cd frontend
npm ci
npm run build

# 3. Sync to S3
aws s3 sync dist/ s3://$bucket --delete

# 4. Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id $dist_id --paths "/*"
```

The `--delete` flag removes files from S3 that are no longer in `dist/`. This
prevents stale hashed assets from accumulating.

---

## Local development

```powershell
# frontend/.env.local (gitignored)
VITE_API_BASE_URL=http://localhost:3000   # local mock server
# or point at the deployed dev API:
VITE_API_BASE_URL=https://abc123.execute-api.us-east-1.amazonaws.com
```

```powershell
cd frontend
npm run dev
```

`import.meta.env.VITE_API_BASE_URL` is available in all component code without
any additional configuration.

---

## Content-Security-Policy

Set CSP headers via a CloudFront response headers policy — not in a `<meta>`
tag. The `<meta>` approach does not protect against all injection vectors.

The `connect-src` directive must include the API Gateway domain:

```hcl
resource "aws_cloudfront_response_headers_policy" "csp" {
  name = "${local.name_prefix}-csp"

  security_headers_config {
    content_security_policy {
      content_security_policy = join("; ", [
        "default-src 'self'",
        "script-src 'self'",
        "connect-src 'self' https://${var.api_gateway_domain}",
        "img-src 'self' data:",
        "style-src 'self' 'unsafe-inline'",
      ])
      override = true
    }
  }
}
```

Attach the policy to the CloudFront distribution's `default_cache_behavior`.

---

## Avoid

- Hardcoding API URLs, region, or Cognito IDs in source files
- Committing `.env.local` or `.env.production` to git
- Using `REACT_APP_*` prefix — that is Create React App convention; Vite uses `VITE_*`
- Running `npm run build` before populating env vars — the bundle will use empty strings
- Setting `VITE_` variables in the shell without a `.env` file for CI — use both for reliability

## See also

- `ai/skills/aws/cloudfront_s3_hosting.md` — S3 bucket and CloudFront infrastructure
- `ai/skills/frontend/api_client_patterns.md` — using `VITE_API_BASE_URL` in the API client
- `ai/skills/aws/api_gateway.md` — API endpoint output to reference in env vars
