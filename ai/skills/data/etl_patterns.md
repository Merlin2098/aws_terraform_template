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

## Anti-patterns

- Embedding SQL in Python
- Skipping validation
- Writing directly to final layer
