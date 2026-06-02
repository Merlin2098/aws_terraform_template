# Python Structured Logging Pattern

## When to use

- Writing Lambda handlers, Glue job scripts, or any Python code that logs to CloudWatch
- Setting up logging configuration for a new pipeline stage
- Writing CloudWatch Insights queries to diagnose production failures

## Core idea

Every log record must contain a fixed set of context fields so that CloudWatch
Insights can filter and aggregate across all stages without knowing the code
structure. Missing fields make log queries unreliable.

---

## Mandatory log field contract

Every log record emitted by pipeline code must include:

| Field | Description | Example |
|---|---|---|
| `timestamp` | ISO 8601, set by the logging formatter | `2025-03-01T14:32:01Z` |
| `level` | Log level string | `INFO`, `ERROR` |
| `service` | Lambda function name or Glue job name | `invoice-processor` |
| `stage` | Pipeline stage | `bronze`, `silver`, `ocr_normalisation` |
| `document_id` | Document being processed | `DOC-2025-001` |
| `correlation_id` | Request trace ID | `abc123` (Lambda request ID) |

Missing any of these fields breaks the Insights queries shown below.

---

## Logging setup

Configure at the module level. Never configure the root logger in library code
— it affects all loggers in the process:

```python
# src/pipeline/logging_config.py
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "service": record.name,
            "message": record.getMessage(),
        }
        # Merge extra fields (document_id, correlation_id, stage, etc.)
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and not key.startswith("_"):
                log_data[key] = value
        return json.dumps(log_data)

def configure_logging(service_name: str) -> logging.Logger:
    logger = logging.getLogger(service_name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
```

---

## Context injection with LoggerAdapter

Use `LoggerAdapter` to inject `document_id`, `correlation_id`, and `stage` into
every log call without modifying each call site:

```python
# src/pipeline/context_logger.py
import logging

class PipelineLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {})
        kwargs["extra"].update(self.extra)
        return msg, kwargs

def get_logger(service: str, stage: str, document_id: str, correlation_id: str):
    base_logger = logging.getLogger(service)
    return PipelineLogger(base_logger, {
        "stage": stage,
        "document_id": document_id,
        "correlation_id": correlation_id,
    })
```

Usage in a Lambda handler:

```python
from pipeline.context_logger import get_logger

def handler(event, context):
    log = get_logger(
        service=context.function_name,
        stage="ocr_normalisation",
        document_id=event.get("document_id", "unknown"),
        correlation_id=context.aws_request_id,
    )
    log.info("Stage started")
    # All subsequent log calls carry document_id, correlation_id, stage
```

---

## Log level discipline

| Level | When to use |
|---|---|
| `DEBUG` | Per-field transformation details, intermediate values |
| `INFO` | Stage entry/exit, record counts, key milestones |
| `WARNING` | Recoverable anomaly — missing optional field, low-confidence score |
| `ERROR` | Exception caught before re-raising — always re-raise after logging |

Never catch an exception, log it, and return a success response. Always re-raise
after logging at ERROR level. Catch-and-swallow hides failures from Step
Functions routing.

---

## CloudWatch Insights sample queries

Use these queries in the CloudWatch console to diagnose pipeline failures.
They assume the mandatory field contract above.

**Find all ERROR logs for a specific document:**

```
fields @timestamp, stage, message, correlation_id
| filter document_id = "DOC-2025-001" and level = "ERROR"
| sort @timestamp asc
```

**Count failures per stage over the last 24 hours:**

```
stats count() as error_count by stage
| filter level = "ERROR"
| sort error_count desc
```

**Trace a document through all stages:**

```
fields @timestamp, level, stage, message
| filter document_id = "DOC-2025-001"
| sort @timestamp asc
```

**Find documents stuck in a stage (no completion log within 5 minutes):**

```
fields @timestamp, document_id, stage
| filter message = "Stage started"
| stats earliest(@timestamp) as start_time by document_id, stage
```

---

## Test pattern

Assert that log output for a known input contains the required fields:

```python
import json
import logging
import pytest
from pipeline.context_logger import get_logger

def test_log_contains_required_fields(caplog):
    with caplog.at_level(logging.INFO):
        log = get_logger("test-svc", "bronze", "DOC-001", "corr-123")
        log.info("Stage started")

    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.stage == "bronze"
    assert record.document_id == "DOC-001"
    assert record.correlation_id == "corr-123"
```

---

## Avoid

- Configuring the root logger in library/pipeline modules — use named loggers only
- `print()` statements in Lambda code — they do not carry structured fields
- Logging sensitive data (PII, full document content) at INFO or above
- Catch-and-log without re-raising — always re-raise after `logger.error()`
- Omitting `stage` or `document_id` — they are required for all Insights queries

## See also

- `ai/skills/aws/cloudwatch_logging.md` — CloudWatch log group setup in Terraform
- `ai/skills/terraform/terraform_observability.md` — log group retention and tagging
- `ai/skills/python/python_testing_quality.md` — caplog usage in pytest
- `ai/skills/python/error_handling_pipeline.md` — structured error payload fields
