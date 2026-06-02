# AWS Athena Query Patterns

## When to use

- Writing Python code that queries Athena from a Lambda or Glue job
- Designing Athena workgroup configuration in Terraform
- Optimising query cost by improving partition pruning

## Core idea

Athena charges per byte scanned. The two levers that reduce cost are partition
pruning (filter on partition columns to skip irrelevant data) and workgroup
guardrails (reject queries that would scan above a threshold). Both must be
configured — Athena has no default limits.

---

## Query lifecycle

Athena queries are asynchronous. `start_query_execution` returns a
`QueryExecutionId`; the result must be polled separately:

```python
import boto3
import time
from pipeline.errors import PermanentError

athena = boto3.client("athena", region_name=settings.aws_region)

def run_query(sql: str, workgroup: str, output_location: str) -> str:
    response = athena.start_query_execution(
        QueryString=sql,
        WorkGroup=workgroup,
        ResultConfiguration={"OutputLocation": output_location},
    )
    return response["QueryExecutionId"]

def wait_for_query(execution_id: str, timeout_seconds: int = 60) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        result = athena.get_query_execution(QueryExecutionId=execution_id)
        state = result["QueryExecution"]["Status"]["State"]
        if state == "SUCCEEDED":
            return result["QueryExecution"]
        if state in ("FAILED", "CANCELLED"):
            reason = result["QueryExecution"]["Status"].get("StateChangeReason", "unknown")
            raise PermanentError(
                stage="athena_query",
                cause=f"Query {state}: {reason}",
            )
        time.sleep(2)
    raise TimeoutError(f"Athena query {execution_id} did not complete within {timeout_seconds}s")
```

Use `timeout_seconds=60` for interactive queries and `timeout_seconds=300` for
batch aggregation queries.

---

## Result retrieval and pagination

`get_query_results` returns up to 1000 rows per call. Use `NextToken` to
paginate for larger result sets:

```python
def fetch_all_rows(execution_id: str) -> list[dict]:
    rows = []
    kwargs = {"QueryExecutionId": execution_id}
    first_page = True
    while True:
        page = athena.get_query_results(**kwargs)
        result_rows = page["ResultSet"]["Rows"]
        if first_page:
            headers = [col["VarCharValue"] for col in result_rows[0]["Data"]]
            result_rows = result_rows[1:]  # skip header row
            first_page = False
        for row in result_rows:
            rows.append({headers[i]: col.get("VarCharValue", "") for i, col in enumerate(row["Data"])})
        token = page.get("NextToken")
        if not token:
            break
        kwargs["NextToken"] = token
    return rows
```

For large result sets (> 10,000 rows), skip `get_query_results` entirely and
read the results file directly from S3 — Athena writes a CSV to the
`output_location` set during `start_query_execution`.

---

## Partition pruning

Always include the partition column in the WHERE clause. Without it, Athena
scans the entire dataset regardless of how many rows match.

For the project's date-partitioned data lake (`partition_date = 'YYYY-MM-DD'`):

```sql
-- Good: partition pruning active
SELECT *
FROM silver.invoices
WHERE partition_date = '2025-03-01'
  AND vendor_name = 'Acme Corp'

-- Bad: full table scan despite the vendor filter
SELECT *
FROM silver.invoices
WHERE vendor_name = 'Acme Corp'
```

After a query completes, log `DataScannedInBytes` to detect pruning failures:

```python
stats = execution["Statistics"]
scanned_mb = stats["DataScannedInBytes"] / 1_048_576
logger.info("Athena query complete", extra={
    "execution_id": execution_id,
    "scanned_mb": round(scanned_mb, 2),
    "execution_time_ms": stats["TotalExecutionTimeInMillis"],
})
if scanned_mb > 1000:
    logger.warning("High data scan — check partition pruning", extra={"execution_id": execution_id})
```

---

## Partition projection

Use Glue catalog partition projection for the date-partitioned data lake instead
of `MSCK REPAIR TABLE`. Projection avoids the full metadata scan cost and works
automatically for new partitions:

```hcl
resource "aws_glue_catalog_table" "silver_invoices" {
  name          = "invoices"
  database_name = aws_glue_catalog_database.silver.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "projection.enabled"              = "true"
    "projection.partition_date.type"  = "date"
    "projection.partition_date.range" = "2024-01-01,NOW"
    "projection.partition_date.format"= "yyyy-MM-dd"
    "storage.location.template"       = "s3://${var.silver_bucket}/invoices/$${partition_date}/"
  }

  partition_keys {
    name = "partition_date"
    type = "string"
  }
  # ... schema definition
}
```

---

## Workgroup configuration

Declare a named workgroup with a bytes-scanned guardrail for each environment:

```hcl
resource "aws_athena_workgroup" "main" {
  name = "${local.name_prefix}-workgroup"
  tags = local.common_tags

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/query-results/"
    }

    bytes_scanned_cutoff_per_query  = 1073741824  # 1 GB — blocks runaway full scans in dev
    enforce_workgroup_configuration = true
    publish_cloudwatch_metrics_enabled = true
  }
}
```

Expose the workgroup name as a Terraform output so Lambda and Glue jobs can
reference it without hardcoding:

```hcl
output "athena_workgroup_name" {
  value       = aws_athena_workgroup.main.name
  description = "Athena workgroup for pipeline queries."
}
```

---

## Avoid

- Queries without a partition column in the WHERE clause — full table scans are expensive
- Using `MSCK REPAIR TABLE` for partition discovery — use partition projection instead
- Hardcoding the workgroup name or output bucket — read from `terraform output`
- Parsing CSV from the S3 result file manually — use `get_query_results` for small sets, pandas/pyarrow for large sets
- Setting no `bytes_scanned_cutoff_per_query` in dev — a runaway query can cost hundreds of dollars

## See also

- `ai/skills/aws/s3_data_lake.md` — S3 bucket structure and partition layout
- `ai/skills/data/data_quality_guidance.md` — validation queries run via Athena
- `ai/skills/sql/sql_workflow_guidance.md` — SQL file organisation for Athena queries
- `ai/skills/terraform/terraform_governance.md` — cost alert for data scanning
