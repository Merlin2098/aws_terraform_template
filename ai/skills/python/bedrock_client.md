# Python Bedrock Client Pattern

## When to use

- Writing Python code that calls Bedrock `invoke_model` or `converse`
- Reviewing pipeline stages that use LLM extraction or generation
- Diagnosing throttling or JSON parsing failures from Bedrock responses

## Core idea

Centralise the model ID and client configuration. Never scatter `boto3.client`
instantiation or model IDs across call sites. Treat LLM output as untrusted
text until validated against the expected schema.

---

## API selection

| API | When to use |
|---|---|
| `converse` | Multi-turn chat, tool use, or when you need a unified message format |
| `invoke_model` | Single extraction tasks in a pipeline — simpler, lower overhead |

For document extraction pipelines (OCR normalisation, invoice parsing), use
`invoke_model`. Reserve `converse` for interactive or multi-step reasoning flows.

---

## Client and model ID management

Centralise configuration in a single module. Never instantiate `boto3.client`
or define the model ID at individual call sites:

```python
# src/clients/bedrock.py
import boto3
import json
from config import settings  # loads from config.yaml

_client = None

def get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    return _client

MODEL_ID = settings.bedrock_model_id  # e.g. "anthropic.claude-3-5-sonnet-20241022-v2:0"
```

In `config.yaml`:

```yaml
bedrock_model_id: "anthropic.claude-3-5-sonnet-20241022-v2:0"
aws_region: "us-east-1"
```

For cross-region inference, set the model ID to the inference profile ARN:

```yaml
bedrock_model_id: "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
```

The Python call site is identical — only the config value changes.

---

## Invocation pattern

```python
import json
from clients.bedrock import get_client, MODEL_ID

def extract_invoice(document_text: str) -> dict:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": (
            "Extract invoice fields and return ONLY valid JSON matching this schema: "
            '{"invoice_number": str|null, "vendor_name": str|null, '
            '"invoice_date": "YYYY-MM-DD"|null, "total_amount": float|null}'
        ),
        "messages": [{"role": "user", "content": document_text}],
    }
    response = get_client().invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    raw = json.loads(response["body"].read())
    return _parse_response(raw)
```

---

## Response parsing

Never assume the LLM output is valid JSON. Always parse defensively:

```python
import re
from pipeline.errors import NormalisationIncomplete

def _parse_response(raw: dict) -> dict:
    text = raw["content"][0]["text"]
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise NormalisationIncomplete(
            stage="bedrock_extraction",
            cause=f"invalid_json: {exc}",
        ) from exc
```

---

## Throttling and retry

Bedrock throttles at the model level. Implement exponential backoff with jitter
and raise a typed exception on exhaustion:

```python
import time
import random
from botocore.exceptions import ClientError
from pipeline.errors import BedrockThrottled

def invoke_with_retry(body: dict, max_retries: int = 3) -> dict:
    delay = 1.0
    for attempt in range(max_retries + 1):
        try:
            response = get_client().invoke_model(
                modelId=MODEL_ID,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            return json.loads(response["body"].read())
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code == "ThrottlingException" and attempt < max_retries:
                sleep = delay * (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(sleep)
                continue
            if code == "ThrottlingException":
                raise BedrockThrottled(stage="bedrock_extraction", cause=str(exc)) from exc
            raise
```

---

## Context window guard

Before invoking, estimate token count to avoid `ValidationException` from
exceeding the model's context window. Use a simple character-based heuristic
(~4 characters per token for English text):

```python
MAX_INPUT_TOKENS = 180_000  # Claude 3.5 Sonnet context window minus output budget

def check_context_length(text: str) -> None:
    estimated_tokens = len(text) // 4
    if estimated_tokens > MAX_INPUT_TOKENS:
        raise ValueError(
            f"Input too long: ~{estimated_tokens} tokens estimated, "
            f"max {MAX_INPUT_TOKENS}"
        )
```

---

## Avoid

- Instantiating `boto3.client("bedrock-runtime")` at call sites — use the shared client module
- Hardcoding the model ID in Python — keep it in config
- Catching `json.JSONDecodeError` silently — always re-raise as a typed pipeline error
- Retrying `PermanentError` or schema validation failures — only retry `ThrottlingException`
- Calling Bedrock without a context window guard on variable-length inputs

## See also

- `ai/skills/aws/bedrock_permissions.md` — IAM setup and model access activation
- `ai/skills/python/error_handling_pipeline.md` — `BedrockThrottled`, `NormalisationIncomplete` definitions
- `ai/skills/python/python_project_guidance.md` — module structure
- `ai/skills/data/etl_patterns.md` — OCR normalisation stage context
