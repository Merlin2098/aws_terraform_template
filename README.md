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
scripts/               Explicit project helpers plus internal hook/testing wrappers
artifacts/             Generated deployment bundles
ai/                    AI guidance and AI context-generation source of truth
tests/                 Lightweight validation
```

## Commands

```bash
make package
make test
make ai-refresh
python scripts/hooks/ai_refresh.py
python install_windows.py --target /path/to/repo --dry-run
python install_linux.py --target /path/to/repo --dry-run
python install_windows.py --target /path/to/repo --local
python install_linux.py --target /path/to/repo --cloud
terraform -chdir=infra init
terraform -chdir=infra plan
terraform -chdir=infra apply
```

## Notes

- `make package` builds `artifacts/data_platform_bundle.zip`
- `requirements.local.txt` installs the local developer environment
- `requirements.cloud.txt` is the deployment/runtime dependency set bundled into artifacts
- `requirements.dev.txt` contains test, lint, and Terraform-quality tooling
- `.ai/` contains optional generated AI context artifacts
- `python scripts/hooks/ai_refresh.py` generates `.ai/context_bundle.yaml`, `.ai/skills_registry.json`, `.ai/dependencies_graph.json`, and `.ai/treemap.md`
- `ai/skills.yaml`, `ai/skills/`, and `ai/context.yaml` are the tracked AI source of truth
- `install_windows.py` is the Windows-friendly installer entrypoint and `install_linux.py` is the CLI installer for Linux or non-GUI environments
- Both installers ask whether to copy the optional `src/`, `infra/`, and `tests/` trees into the host repository
- Both installers also ask whether the host project is `local` or `cloud` unless `--local` or `--cloud` is passed explicitly
- Local installs copy `requirements.local.txt` and `requirements.dev.txt`, but skip `requirements.cloud.txt`
- Cloud installs copy `requirements.local.txt`, `requirements.cloud.txt`, and `requirements.dev.txt`
- The installer does not create or modify the host project's `requirements.txt`
- The cloud profile stays superset-style so teams can start with a local MVP and later add cloud runtime dependencies without reinstalling the template
- Hook helpers live under `scripts/hooks/` and quality wrappers live under `scripts/testing/` so they stay distinct from host-project operational scripts
- Run Terraform directly from `infra/` for infrastructure changes
- Automatic pre-commit is limited to AI refresh and dependency sync; Ruff lint, formatting, and pytest remain explicit or manual checks
