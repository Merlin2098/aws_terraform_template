# Data Quality Guidance

Use this guidance when adding validation to Python, SQL, or AWS data workflows.

Keep checks close to the data contract:

- Validate required columns, types, nullability, key uniqueness, ranges, and accepted values.
- Separate blocking quality gates from advisory profiling.
- Make checks deterministic and runnable locally when possible.
- Store quality failures with enough context to debug without exposing sensitive data.
- Test both valid and intentionally invalid sample data.

For this template, define where validation runs explicitly:

- Python job code in `src/jobs/`
- SQL transformation boundaries in `src/transformations/`
- Contract checks aligned with files in `src/contracts/`
- AWS execution points such as Glue, Lambda, Athena, or orchestrated pipeline steps

Make failed validation behavior explicit so downstream consumers know whether the pipeline should stop, retry, or emit a partial result.
