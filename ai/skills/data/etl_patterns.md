# ETL Pipeline Pattern

## Layers

- Bronze: raw ingestion
- Silver: cleaned data
- Gold: business-ready data

## Flow

1. Ingest raw data
2. Validate schema
3. Apply transformations
4. Store optimized output

## Best practices

- Separate logic (SQL) from execution (Python)
- Use config-driven pipelines
- Validate early (contracts)
- Use Parquet for storage

## OCR Normalisation Stage

OCR normalisation is a Bronze → Silver transformation where a raw document (image or PDF) is converted to structured data using Textract + Bedrock. Apply these patterns within the standard ETL flow.

### Prompt template versioning

Store the prompt version as a config key, not inline in the Lambda or job code:

```python
# config.yaml
ocr_normalisation:
  prompt_version: "v3"
  prompt_path: "prompts/invoice_extraction_v3.txt"
```

Load the prompt file explicitly at runtime. Never embed the full prompt string in Python code — it makes version tracking and regression testing impossible.

### Output schema contract

Define the expected extraction fields explicitly. The LLM response must conform to this schema before promotion to Silver:

```json
{
  "invoice_number": "string | null",
  "vendor_name":    "string | null",
  "invoice_date":   "YYYY-MM-DD | null",
  "total_amount":   "number | null",
  "line_items":     "[{ description, quantity, unit_price }]"
}
```

Always validate the parsed JSON against this schema immediately after parsing. A missing required field is a `NormalisationIncomplete` error, not a silent null.

### Confidence threshold routing

After extraction, compute a confidence score from the number of non-null required fields:

- Score ≥ 0.85 → auto-promote to Silver layer
- Score < 0.85 → route to human review queue (SQS DLQ pattern — see `ai/skills/aws/sqs_patterns.md`)

Never silently promote a low-confidence record to Silver.

### Partial extraction handling

When required fields are missing or the LLM returns invalid JSON, raise a typed `NormalisationIncomplete` exception (defined in `ai/skills/python/error_handling_pipeline.md`) with the following payload:

```python
raise NormalisationIncomplete(
    stage="ocr_normalisation",
    document_id=doc_id,
    correlation_id=correlation_id,
    cause="missing_fields: invoice_number, total_amount"
)
```

Step Functions catches this error class and routes to the human review branch.

### Regression fixture pattern

Keep a `fixtures/ocr_samples/` directory with known-good input/output pairs:

```
fixtures/ocr_samples/
├── invoice_standard/
│   ├── input.json        # Textract block output
│   └── expected.json     # expected extraction result
├── invoice_handwritten/
│   ├── input.json
│   └── expected.json
```

Run these fixtures in CI as part of `python/python_testing_quality.md` test coverage.

---

## Anti-patterns

- Embedding SQL in Python
- Skipping validation
- Writing directly to final layer
- Inlining prompt templates as Python string literals
- Silently promoting low-confidence OCR extractions to Silver
