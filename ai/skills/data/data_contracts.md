# Data Contracts Pattern

## Purpose

Ensure data quality and consistency across pipelines.

## Structure

- Schema definition
- Required fields
- Data types
- Constraints

## Example

- id: string (required)
- date: date
- amount: float

## Validation points

- After ingestion (bronze)
- Before transformation (silver)
- Before exposure (gold)

## Benefits

- Early error detection
- Stable downstream systems
- Better governance
