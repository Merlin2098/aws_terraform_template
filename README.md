# AWS + Terraform Data Engineering Template

This repository is a minimal template for packaging Python data jobs and deploying AWS infrastructure with Terraform.

There is no runtime dependency on generated AI context, no skill orchestration, and no AI logic in execution.

## Structure

```text
infra/                 Terraform for AWS infrastructure
src/jobs/              Python job entrypoints
src/transformations/   SQL transformations
src/config/            Runtime configuration
src/contracts/         Data contracts
scripts/               Explicit packaging helpers
artifacts/             Generated deployment bundles
ai/                    AI guidance and AI context-generation source of truth
tests/                 Lightweight validation
```

## Commands

```bash
make package
make test
make ai-refresh
python scripts/ai_refresh.py --light
python main.py --target /path/to/repo --dry-run
python install_template_linux.py --target /path/to/repo --dry-run
terraform -chdir=infra init
terraform -chdir=infra plan
terraform -chdir=infra apply
```

## Notes

- `make package` builds `artifacts/data_platform_bundle.zip`
- `.ai/` contains optional generated AI context artifacts
- `ai/skills.yaml`, `ai/skills/`, and `ai/context.yaml` are the tracked AI source of truth
- `main.py` is the Windows-friendly installer entrypoint and `install_template_linux.py` is the CLI installer for Linux or non-GUI environments
- The installer mirrors the tracked template files and does not force empty `src/` or `infra/` subdirectories
- Run Terraform directly from `infra/` for infrastructure changes
- Pre-commit is limited to lint, format, and manual test execution
