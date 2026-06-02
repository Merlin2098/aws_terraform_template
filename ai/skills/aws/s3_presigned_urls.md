# AWS S3 Presigned URL Pattern

## When to use

- Generating presigned URLs in Lambda for direct browser-to-S3 uploads
- Allowing clients to download private S3 objects without exposing credentials
- Implementing the backend side of the file upload flow

## Core idea

A presigned URL delegates specific S3 access to a bearer — anyone with the URL
can perform the operation for the URL's lifetime. Generate URLs only after
validating the caller's identity. Log every generation event with the user
identity and `document_id`.

---

## PUT vs POST presigned operations

| Method | Use when |
|---|---|
| `generate_presigned_url` for `put_object` | Simple file upload — browser sends the file directly |
| `generate_presigned_post` | Server-side file size and content-type enforcement at S3 level |

For this project, use `generate_presigned_post` — it allows the Lambda to
enforce maximum file size in the presigned conditions, preventing oversized
uploads from reaching S3:

```python
import boto3
from botocore.config import Config

s3 = boto3.client("s3", region_name=settings.aws_region, config=Config(signature_version="s3v4"))

def generate_upload_url(bucket: str, key: str, content_type: str, max_size_bytes: int) -> dict:
    return s3.generate_presigned_post(
        Bucket=bucket,
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, max_size_bytes],
        ],
        ExpiresIn=600,  # 10 minutes
    )
```

The response contains `url` and `fields` — the frontend must POST both as
`multipart/form-data` (not a simple PUT):

```javascript
const { url, fields } = await client.post('/upload/presign', { filename, contentType }).then(r => r.data)
const formData = new FormData()
Object.entries(fields).forEach(([k, v]) => formData.append(k, v))
formData.append('file', file)
await fetch(url, { method: 'POST', body: formData })
```

If using `generate_presigned_url` (PUT), the frontend sends the raw file body
directly to the presigned URL without form fields.

---

## TTL selection

| Scenario | Recommended TTL |
|---|---|
| Interactive upload (user waiting) | 300–600 seconds |
| Batch / automated upload | 60–120 seconds |
| Large file (> 50 MB) on slow connection | 900 seconds |
| Maximum allowed | 3600 seconds |

Never exceed 3600 seconds for upload URLs. Shorter TTLs reduce the window for
misuse if a URL is leaked.

---

## CORS on the upload bucket

The upload bucket requires a CORS rule to allow browser requests. This is
separate from CloudFront CORS:

```hcl
resource "aws_s3_bucket_cors_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  cors_rule {
    allowed_headers = ["Content-Type", "x-amz-*"]
    allowed_methods = ["PUT", "POST"]
    allowed_origins = [var.frontend_origin]  # e.g. "https://d1234.cloudfront.net"
    expose_headers  = ["ETag"]
    max_age_seconds = 300
  }
}
```

---

## Lambda IAM

The Lambda generating presigned URLs needs `s3:PutObject` scoped to the upload
prefix only — not the entire bucket:

```hcl
data "aws_iam_policy_document" "presign_lambda" {
  statement {
    sid     = "S3PutUploadPrefix"
    effect  = "Allow"
    actions = ["s3:PutObject"]
    resources = [
      "${aws_s3_bucket.uploads.arn}/uploads/*",
    ]
  }
}
```

---

## Security

A presigned URL is not bound to the requester's identity — anyone with the URL
can upload. Mitigate this by:

1. Generating URLs only after validating the user's auth token in the Lambda
2. Including the user's identity in the S3 key path (e.g., `uploads/{user_id}/{document_id}`)
3. Setting a short TTL
4. Logging every URL generation with `document_id` and user identity

```python
logger.info(
    "Presigned URL generated",
    extra={
        "document_id": document_id,
        "user_id": user_id,
        "bucket": bucket,
        "key": key,
        "expires_in": 600,
    },
)
```

---

## S3 event trigger

After the upload completes, S3 fires `s3:ObjectCreated:Put` (or `Post`) to
start the pipeline. Configure this via EventBridge or a direct S3 notification:

```hcl
resource "aws_s3_bucket_notification" "upload_trigger" {
  bucket = aws_s3_bucket.uploads.id

  queue {
    queue_arn     = aws_sqs_queue.pipeline_input.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "uploads/"
  }
}
```

---

## Avoid

- Generating presigned URLs without first validating the caller's auth token
- TTL > 3600 seconds — the maximum S3 supports with SigV4
- Scoping the Lambda IAM policy to the entire bucket — use the upload prefix
- Forgetting the CORS rule on the upload bucket — uploads fail silently in the browser
- Using the same bucket for uploads (Bronze) and processed data (Silver/Gold) — separate buckets enforce stage isolation

## See also

- `ai/skills/frontend/file_upload_ux.md` — browser-side upload implementation
- `ai/skills/aws/s3_data_lake.md` — bucket structure and access patterns
- `ai/skills/terraform/iam_least_privilege.md` — IAM scoping principles
- `ai/skills/aws/sqs_patterns.md` — SQS trigger for the upload notification
