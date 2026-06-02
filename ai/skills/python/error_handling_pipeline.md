# Python Pipeline Error Handling Pattern

## When to use

- Writing Lambda handlers or pipeline stage code that runs inside Step Functions
- Designing the `Catch` blocks in a Step Functions state machine definition
- Reviewing error routing between pipeline stages

## Core idea

Step Functions routes errors by the Python exception class name. Use a typed
exception hierarchy so that `Catch.ErrorEquals` in the state machine definition
matches exactly what Python raises — never catch-and-swallow, and never use
generic `Exception` for routing decisions.

---

## Exception hierarchy

Define a shared exceptions module used by all pipeline stages:

```python
# src/pipeline/errors.py

class PipelineError(Exception):
    """Base class for all pipeline errors. Carries structured context."""

    def __init__(self, stage: str, cause: str, document_id: str = "", correlation_id: str = ""):
        self.stage = stage
        self.cause = cause
        self.document_id = document_id
        self.correlation_id = correlation_id
        super().__init__(f"[{stage}] {cause}")


class TransientError(PipelineError):
    """Retry-safe error. Network failures, throttling, temporary service unavailability."""


class PermanentError(PipelineError):
    """Non-retryable error. Schema violations, invalid document type, missing required config."""


class NormalisationIncomplete(PipelineError):
    """Partial extraction — required fields missing or LLM output unparseable. Route to human review."""


class BedrockThrottled(TransientError):
    """Bedrock ThrottlingException exhausted all retries."""
```

---

## How Step Functions reads Python exceptions

When a Lambda raises an exception, Step Functions captures the exception class
name as the `Error` field in the execution event. The `Catch` block in the
state machine matches against this name:

```json
"Catch": [
  {
    "ErrorEquals": ["NormalisationIncomplete"],
    "Next": "RouteToHumanReview"
  },
  {
    "ErrorEquals": ["TransientError", "BedrockThrottled"],
    "Next": "RetryWithBackoff"
  },
  {
    "ErrorEquals": ["PermanentError"],
    "Next": "SendToDLQ"
  },
  {
    "ErrorEquals": ["States.ALL"],
    "Next": "HandleUnexpectedError"
  }
]
```

The string in `ErrorEquals` must exactly match the Python class name. If the
class is renamed, the state machine `Catch` block breaks silently (falls through
to `States.ALL`). Keep exception class names stable and treat them as part of
the state machine interface.

---

## Distinguishing transient from permanent failures

| Error type | Examples | Action |
|---|---|---|
| Transient | `ThrottlingException`, `ServiceUnavailableException`, network timeout | Retry with backoff; raise `TransientError` after max retries |
| Permanent | Schema violation, missing required field, unsupported file type | Do not retry; raise `PermanentError` immediately |
| Incomplete | LLM returned invalid JSON or low-confidence extraction | Route to human review queue; raise `NormalisationIncomplete` |

Never retry a `PermanentError`. Never silence a `NormalisationIncomplete` by
promoting the partial result to Silver.

---

## Structured error payload

Every raised exception must carry enough context to diagnose the failure without
reading CloudWatch logs manually:

```python
raise PermanentError(
    stage="schema_validation",
    document_id=doc_id,
    correlation_id=correlation_id,
    cause="missing_required_field: invoice_number",
)
```

The `stage`, `document_id`, and `correlation_id` fields are also the minimum
required fields for structured logging (see `ai/skills/python/logging_structured.md`).

---

## Lambda handler pattern

```python
import logging
from pipeline.errors import PermanentError, NormalisationIncomplete

logger = logging.getLogger(__name__)

def handler(event, context):
    doc_id = event.get("document_id", "unknown")
    correlation_id = event.get("correlation_id", context.aws_request_id)
    try:
        result = process_document(event, doc_id, correlation_id)
        return {"status": "ok", "document_id": doc_id, **result}
    except (PermanentError, NormalisationIncomplete):
        logger.error("Non-retryable failure", extra={"document_id": doc_id})
        raise  # Step Functions Catch block handles routing
    except Exception as exc:
        logger.error("Unexpected error: %s", exc, extra={"document_id": doc_id})
        raise  # Falls through to States.ALL
```

Do not catch-and-return error payloads as successful responses. Step Functions
must see a raised exception to trigger `Catch` routing.

---

## Step Functions Catch vs Lambda destinations

| Mechanism | When to use |
|---|---|
| Step Functions `Catch` | Lambda runs inside a state machine — preferred for pipeline routing |
| Lambda destinations (on-failure) | Standalone Lambda invocations outside Step Functions |

Never use Lambda destinations as an alternative to Step Functions `Catch` when
the Lambda is already a state machine task. The two mechanisms are not
additive — they target different invocation contexts.

---

## Avoid

- Using `except Exception` for routing decisions — match the specific class name
- Catch-and-return: catching an error and returning a "failed" success response instead of raising
- Renaming exception classes without updating all `Catch.ErrorEquals` lists in state machine definitions
- Missing `document_id` and `correlation_id` in raised exceptions — they are required for log tracing

## See also

- `ai/skills/aws/step_functions.md` — state machine structure and retry configuration
- `ai/skills/python/bedrock_client.md` — `BedrockThrottled` raise point
- `ai/skills/aws/sqs_patterns.md` — DLQ routing for `PermanentError`
- `ai/skills/python/python_testing_quality.md` — testing error paths
