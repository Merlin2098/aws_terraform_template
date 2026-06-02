# AWS SQS Patterns

## When to use

- Configuring SQS queues as Lambda event sources
- Setting up dead-letter queues for pipeline error routing
- Decoupling asynchronous pipeline stages (e.g., Textract completion → normalisation)

## Core idea

SQS decouples producers from consumers. The three settings that cause the most
production failures are: under-sized visibility timeout (duplicate processing),
missing DLQ (silent message loss), and over-sized batch (partial failure routing
without `ReportBatchItemFailures`). Configure all three explicitly.

---

## Visibility timeout

Set the visibility timeout to at least **6× the Lambda timeout**. If Lambda
times out during processing, SQS will re-deliver the message before Lambda has
finished — causing duplicate processing.

```hcl
resource "aws_sqs_queue" "pipeline_input" {
  name                       = "${local.name_prefix}-pipeline-input"
  visibility_timeout_seconds = 180  # Lambda timeout is 30s → 6x = 180s
  message_retention_seconds  = 86400  # 1 day
  tags                       = local.common_tags
}
```

---

## Dead-letter queue

Every queue must have a `redrive_policy` that routes failed messages to a DLQ
after `maxReceiveCount` delivery attempts. The DLQ must have a longer retention
period than the source queue so that failed messages are available for inspection
before they expire.

```hcl
resource "aws_sqs_queue" "pipeline_dlq" {
  name                      = "${local.name_prefix}-pipeline-dlq"
  message_retention_seconds = 1209600  # 14 days
  tags                      = local.common_tags
}

resource "aws_sqs_queue" "pipeline_input" {
  name                       = "${local.name_prefix}-pipeline-input"
  visibility_timeout_seconds = 180
  message_retention_seconds  = 86400

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.pipeline_dlq.arn
    maxReceiveCount     = 3
  })

  tags = local.common_tags
}
```

---

## Lambda event source mapping

Use `ReportBatchItemFailures` to allow partial batch success. Without it, a
single failed message causes the entire batch to retry:

```hcl
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn                   = aws_sqs_queue.pipeline_input.arn
  function_name                      = aws_lambda_function.processor.arn
  batch_size                         = 1
  function_response_types            = ["ReportBatchItemFailures"]
  enabled                            = true
}
```

Start with `batch_size = 1` for new pipelines. Only increase after confirming
that the Lambda handler is fully idempotent.

Return failed item identifiers from the Lambda to trigger partial batch failure:

```python
def handler(event, context):
    failures = []
    for record in event["Records"]:
        try:
            process(record)
        except Exception:
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}
```

---

## FIFO vs standard queues

| Type | When to use |
|---|---|
| Standard | High-throughput async processing — ETL pipelines, Textract callbacks, upload events |
| FIFO | Strict ordering required, exactly-once processing needed (rare in ETL) |

Default to standard queues for this project's pipeline patterns. FIFO queues
have lower throughput limits and require a `MessageGroupId` on every send call.

---

## Outputs

Expose queue URL and ARN as module outputs so downstream resources can
reference them from `terraform output`:

```hcl
output "queue_url" {
  value       = aws_sqs_queue.pipeline_input.url
  description = "SQS queue URL for pipeline input messages."
}

output "queue_arn" {
  value       = aws_sqs_queue.pipeline_input.arn
  description = "SQS queue ARN for event source mappings and IAM policies."
}

output "dlq_arn" {
  value       = aws_sqs_queue.pipeline_dlq.arn
  description = "Dead-letter queue ARN for failed message inspection."
}
```

---

## Avoid

- Setting `visibility_timeout_seconds` lower than 6× the Lambda timeout
- Queues without a `redrive_policy` — messages disappear silently on repeated failures
- `batch_size > 1` without `ReportBatchItemFailures` — one failure retries the entire batch
- FIFO queues for high-throughput ETL — throughput limits will cause throttling at scale
- Hardcoding queue URLs or ARNs — always read from `terraform output`

## See also

- `ai/skills/aws/lambda_functions.md` — Lambda configuration and timeouts
- `ai/skills/python/error_handling_pipeline.md` — exception types routed to DLQ
- `ai/skills/aws/eventbridge.md` — alternative event routing for lower-volume triggers
- `ai/skills/terraform/terraform_governance.md` — cost alert for SQS request volume
