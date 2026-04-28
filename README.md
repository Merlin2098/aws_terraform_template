# AWS + Terraform Data Engineering Template

This repository is a minimal template for packaging Python data jobs and deploying AWS infrastructure with Terraform.

There is no Tinker runtime, no generated context, no skill orchestration, and no AI logic in execution.

## Structure

```text
infra/                 Terraform for AWS infrastructure
src/jobs/              Python job entrypoints
src/transformations/   SQL transformations
src/config/            Runtime configuration
src/contracts/         Data contracts
scripts/               Explicit packaging helpers
artifacts/             Generated deployment bundles
ai/skills.yaml         Optional human-readable implementation hints
tests/                 Lightweight validation
```

## Commands

```bash
make package
make test
make deploy
```

## Notes

- `make package` builds `artifacts/data_platform_bundle.zip`
- `make deploy` runs Terraform from `infra/`
- Pre-commit is limited to lint, format, and manual test execution
