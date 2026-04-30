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
- `python scripts/ai_refresh.py --light` generates `.ai/context_bundle.yaml`, `.ai/skills_registry.json`, and `.ai/treemap.md`
- `python scripts/ai_refresh.py --full` also adds `.ai/dependencies_graph.json`
- `ai/skills.yaml`, `ai/skills/`, and `ai/context.yaml` are the tracked AI source of truth
- `install_windows.py` is the Windows-friendly installer entrypoint and `install_linux.py` is the CLI installer for Linux or non-GUI environments
- Both installers ask whether to copy the optional `src/`, `infra/`, and `tests/` trees into the host repository
- Both installers also ask whether the host project is `local` or `cloud` unless `--local` or `--cloud` is passed explicitly
- Local installs merge `requirements.local.txt` and `requirements.dev.txt` into the host `requirements.txt`
- Cloud installs merge `requirements.local.txt`, `requirements.cloud.txt`, and `requirements.dev.txt` into the host `requirements.txt`
- Local installs copy `requirements.local.txt` and `requirements.dev.txt`, but skip `requirements.cloud.txt`
- Cloud installs copy `requirements.local.txt`, `requirements.cloud.txt`, and `requirements.dev.txt`
- The cloud profile is intentionally superset-style so teams can start with a local MVP and later add cloud runtime dependencies without reinstalling the template
- Run Terraform directly from `infra/` for infrastructure changes
- Automatic pre-commit is limited to AI refresh and dependency sync; Ruff lint, formatting, and pytest remain explicit or manual checks
