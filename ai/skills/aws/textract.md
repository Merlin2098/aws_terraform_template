# AWS Textract Pattern

## When to use

- Implementing document analysis for invoices, forms, or scanned PDFs
- Choosing between synchronous and asynchronous Textract workflows
- Wiring up Textract completion notifications to downstream pipeline stages

## Core idea

For multi-page or TIF documents (the primary use case in this project), always
use the asynchronous API. Use SNS + SQS notification instead of polling to avoid
Lambda timeout failures on slow jobs.

---

## Sync vs async selection

| API | When to use |
|---|---|
| `detect_document_text` / `analyze_document` (sync) | Single-page JPEG/PNG/PDF, ≤ 5 MB, latency-sensitive |
| `start_document_analysis` / `get_document_analysis` (async) | Multi-page documents, TIF files, PDF > 5 MB — required for this project |

Always use async for the invoice pipeline. Sync calls on multi-page documents
return an error at the API level.

---

## Asynchronous job flow

### Option A: SNS + SQS notification (preferred)

Textract publishes to an SNS topic on job completion. An SQS queue subscribes to
the topic. A Lambda processes the notification and fetches results.

```
[S3 upload] → start_document_analysis(SNSTopicArn)
           → Textract runs async
           → Textract publishes to SNS on SUCCEEDED/FAILED
           → SNS → SQS → Lambda → get_document_analysis(JobId)
```

This avoids polling Lambda timeouts for long-running jobs (multi-page documents
can take 30–120 seconds).

### Option B: Polling (fallback only)

```python
import time
from botocore.exceptions import ClientError

def wait_for_job(client, job_id: str, timeout: int = 120) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get_document_analysis(JobId=job_id)
        status = response["JobStatus"]
        if status == "SUCCEEDED":
            return response
        if status == "FAILED":
            raise RuntimeError(f"Textract job failed: {response.get('StatusMessage')}")
        time.sleep(5)
    raise TimeoutError(f"Textract job {job_id} did not complete within {timeout}s")
```

Use polling only in one-off scripts or when SNS/SQS infrastructure is not yet
available. Never use polling inside a Lambda that has a 30 s timeout.

---

## FeatureTypes selection

Only request the feature types your normalisation stage actually uses:

| FeatureType | Use when | Cost |
|---|---|---|
| `TABLES` | Document contains structured table data | Higher per-page charge |
| `FORMS` | Document contains key-value pairs (form fields) | Higher per-page charge |
| *(omit both)* | Text extraction only (invoices with free-form layout) | Base rate |

For invoice extraction where text layout is free-form, start without
`FeatureTypes` and add `FORMS` only if key-value extraction improves accuracy.

```python
response = client.start_document_analysis(
    DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}},
    FeatureTypes=["FORMS"],  # only if key-value pairs are needed
    NotificationChannel={
        "SNSTopicArn": sns_topic_arn,
        "RoleArn": textract_sns_role_arn,
    },
)
job_id = response["JobId"]
```

---

## Block/Relationship schema

Textract returns a list of `Block` objects. The types relevant to invoice
extraction:

| BlockType | Description |
|---|---|
| `PAGE` | Container for all blocks on a page |
| `LINE` | A line of text |
| `WORD` | Individual word with `Text` and `Confidence` fields |
| `KEY_VALUE_SET` | Form field key or value (requires `FORMS` feature) |
| `TABLE` / `CELL` | Table structure (requires `TABLES` feature) |

To extract plain text from a job result, concatenate `LINE` blocks in page order.

---

## IAM actions

```hcl
data "aws_iam_policy_document" "textract" {
  statement {
    sid    = "TextractAnalyse"
    effect = "Allow"
    actions = [
      "textract:StartDocumentAnalysis",
      "textract:GetDocumentAnalysis",
      "textract:DetectDocumentText",
    ]
    resources = ["*"]  # Textract does not support resource-level restrictions
  }

  statement {
    sid     = "S3ReadSource"
    effect  = "Allow"
    actions = ["s3:GetObject"]
    resources = [
      "${aws_s3_bucket.bronze.arn}/documents/*",
    ]
  }

  statement {
    sid     = "SNSPublishCompletion"
    effect  = "Allow"
    actions = ["sns:Publish"]
    resources = [aws_sns_topic.textract_notifications.arn]
  }
}
```

Note: Textract requires a separate IAM role with `sns:Publish` permission passed
via `NotificationChannel.RoleArn` — this is not the Lambda's execution role. The
role must also have a trust policy allowing `textract.amazonaws.com` to assume it.

---

## Cost awareness

Log the page count for every job. Page count drives cost directly:

```python
pages = sum(1 for b in blocks if b["BlockType"] == "PAGE")
logger.info("Textract job complete", extra={"job_id": job_id, "page_count": pages})
```

Set a budget alert for Textract in `terraform_governance.md`. At scale, a single
100-page document costs ~$1.50 with `FORMS` enabled.

---

## Terraform resources

```hcl
resource "aws_sns_topic" "textract_notifications" {
  name = "${local.name_prefix}-textract-notifications"
  tags = local.common_tags
}

resource "aws_iam_role" "textract_sns" {
  name = "${local.name_prefix}-textract-sns-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "textract.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = local.common_tags
}
```

---

## Avoid

- Using sync API for multi-page documents — returns an API error
- Polling inside a Lambda with a short timeout — use SNS/SQS notification instead
- Requesting `TABLES` and `FORMS` when only plain text is needed — unnecessary cost
- Hardcoding `JobId` — always pass it through the pipeline event payload
- Omitting page count logging — makes per-document cost invisible

## See also

- `ai/skills/aws/sqs_patterns.md` — SQS subscription to SNS for completion events
- `ai/skills/aws/bedrock_permissions.md` — cost section for per-service budget alerts
- `ai/skills/data/etl_patterns.md` — OCR normalisation stage that consumes Textract output
- `ai/skills/terraform/terraform_governance.md` — Textract cost alert setup
