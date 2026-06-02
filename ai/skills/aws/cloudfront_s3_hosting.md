# AWS CloudFront + S3 Static Hosting Pattern

## When to use

- Hosting a static SPA (React, Vite) on S3 + CloudFront
- Replacing or upgrading an existing OAI-based CloudFront distribution
- Configuring SPA routing so client-side paths return `index.html`

## Core idea

S3 serves the static assets; CloudFront caches and distributes them globally.
The S3 bucket must never be publicly accessible — CloudFront accesses it via
Origin Access Control (OAC). Cache behavior must be split between immutable
hashed assets (long TTL) and `index.html` (no cache) so deploys are visible
immediately.

---

## OAC vs OAI

OAI (Origin Access Identity) is deprecated. Always use OAC for new distributions.

```hcl
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${local.name_prefix}-oac"
  description                       = "OAC for ${local.name_prefix} frontend bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}
```

---

## S3 bucket setup

The bucket must block all public access. Do not add a public-access bucket
policy — CloudFront accesses S3 using the OAC service principal:

```hcl
resource "aws_s3_bucket" "frontend" {
  bucket = "${local.name_prefix}-frontend"
  tags   = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_oac.json
}

data "aws_iam_policy_document" "frontend_oac" {
  statement {
    sid     = "AllowCloudFrontOAC"
    effect  = "Allow"
    actions = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.frontend.arn]
    }
  }
}
```

---

## CloudFront distribution

```hcl
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"  # US/Europe only — cheaper for dev
  tags                = local.common_tags

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  # Hashed assets: long TTL — Vite content-hashes filenames on every build
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    min_ttl     = 0
    default_ttl = 86400    # 1 day
    max_ttl     = 31536000  # 1 year
  }

  # index.html: no-cache so deploys are immediately visible
  ordered_cache_behavior {
    path_pattern           = "/index.html"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  # SPA routing: 403/404 from S3 → return index.html with HTTP 200
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
```

---

## Cache invalidation after deploy

After every `aws s3 sync`, invalidate the CloudFront cache to force edge
refresh. Read the distribution ID from `terraform output` — never hardcode it:

```powershell
# scripts/deploy_frontend.ps1
$bucket   = terraform -chdir=infra output -raw frontend_bucket_name
$dist_id  = terraform -chdir=infra output -raw cloudfront_distribution_id

aws s3 sync dist/ s3://$bucket --delete
aws cloudfront create-invalidation --distribution-id $dist_id --paths "/*"
```

To reduce invalidation cost, invalidate only `/index.html` when only the app
entry point changed (common for hotfixes):

```powershell
aws cloudfront create-invalidation --distribution-id $dist_id --paths "/index.html"
```

---

## Outputs

Expose all values needed by deployment scripts and the frontend build:

```hcl
output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.frontend.id
  description = "CloudFront distribution ID — required for cache invalidation after deploy."
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.frontend.domain_name
  description = "CloudFront domain name — set as VITE_APP_URL in frontend build."
}

output "frontend_bucket_name" {
  value       = aws_s3_bucket.frontend.bucket
  description = "S3 bucket name — target for aws s3 sync."
}
```

---

## Avoid

- Using OAI for new distributions — it is deprecated; use OAC
- Setting a long TTL on `index.html` — deploys will not be visible until TTL expires
- Making the S3 bucket publicly accessible — CloudFront + OAC is the correct access pattern
- Forgetting the custom error response for 403/404 — SPA routes will return S3 error pages
- Hardcoding distribution ID or bucket name in deploy scripts — read from `terraform output`

## See also

- `ai/skills/frontend/react_vite_aws.md` — frontend build and deploy sequence
- `ai/skills/terraform/terraform_observability.md` — log group patterns
- `ai/skills/terraform/terraform_governance.md` — tagging and cost alert
- `ai/skills/terraform/terraform_security.md` — encryption and access control
