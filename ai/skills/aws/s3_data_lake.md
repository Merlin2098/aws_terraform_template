# S3 Data Lake Pattern

## When to use

- Storing raw and processed data
- Data lake architectures

## Core idea

Use S3 as the central storage layer.

## Structure

- bronze/ → raw
- silver/ → cleaned
- gold/ → analytics

## Best practices

- Use Parquet format
- Partition by date or domain
- Apply lifecycle policies
- Enable versioning

## Security

- Block public access
- Enable encryption (KMS)

## Avoid

- Flat file structure
- Mixing layers
