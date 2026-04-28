# Glue Job Pattern

## When to use

- Batch ETL pipelines
- S3 → S3 transformations
- Structured data processing (Parquet, CSV)

## Architecture

- Input: S3 (bronze)
- Processing: Glue (Spark or Python shell)
- Output: S3 (silver/gold)

## Structure

- Script entrypoint (Python)
- External SQL (optional)
- Config-driven execution

## Best practices

- Use Parquet for output
- Partition by date or domain keys
- Avoid schema inference in production
- Log to CloudWatch
- Use job bookmarks for incremental loads

## Common errors

- Missing IAM permissions (S3, logs)
- Temp directory not defined
- Large memory consumption (bad partitioning)

## Terraform pattern

- aws_glue_job
- aws_iam_role
- S3 script upload
