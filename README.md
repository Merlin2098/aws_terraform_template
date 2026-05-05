# AWS + Terraform Data Engineering Template

This repository is a starter template for AWS-oriented data engineering
projects. It helps teams bootstrap a host repository with explicit Python, SQL,
Terraform, config, testing, and AI-guidance scaffolding instead of rebuilding
the same project conventions from scratch each time.

It is designed for teams that want a reproducible starting point for local or
cloud-oriented data-platform work without introducing hidden orchestration or
runtime AI dependencies.

## What Problem It Solves

Starting a new data engineering repository often means re-deciding the same
basics:

* how Python packaging and deployment bundles should work
* how SQL, config, infrastructure, and tests should be organized
* how local and cloud dependency profiles should be separated
* how AI guidance files should live in the repo without becoming runtime logic
* how to support Windows-restricted environments alongside standard shell flows

This template solves that by giving you a consistent installation path and a
simple operational model that can be copied into a host repository.

## Current Status

The template currently supports:

* installation into another repository through Windows and Linux installer entrypoints
* host setup for either `pip` or `uv`
* `local` and `cloud` dependency profiles
* optional copying of `src/`, `infra/`, and `tests/`
* explicit project commands for packaging, tests, and AI refresh
* Windows corporate workflows where `make.exe` may not be available in `PATH`

There is no runtime dependency on generated AI context, no skill orchestration,
and no AI logic in execution.

## How It Works

At a high level, teams use this template in four steps:

1. Install the template into a host repository.
2. Choose whether the host project is `local` or `cloud`.
3. Choose whether the host manages dependencies with `pip` or `uv`.
4. Use explicit commands for packaging, tests, AI refresh, and Terraform work.

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

## Common Commands

```bash
make package
make test
make ai-refresh
./scripts/windows/setup_env.ps1
./scripts/windows/update_venv.ps1
./scripts/windows/run_make.ps1 test
python scripts/hooks/ai_refresh.py
python install_windows.py --target /path/to/repo --dry-run
python install_linux.py --target /path/to/repo --dry-run
terraform -chdir=infra init
terraform -chdir=infra plan
```

For Windows-specific `make` usage, including corporate environments where
`make.exe` is not in `PATH`, see `docs/windows_setup/`.

## Installation Model

The template is installed into a host repository with:

* `install_windows.py` for Windows-friendly setup
* `install_linux.py` for Linux and non-GUI environments

Both installers can:

* preview changes with `--dry-run`
* choose `local` or `cloud`
* choose `pip` or `uv`
* optionally include the starter `src/`, `infra/`, and `tests/` trees

The installer copies template files into the host repository, but it does not:

* run Terraform
* install dependencies in the host
* initialize Git
* execute pre-commit in the host

## Dependency Model

The template supports two host dependency workflows.

For `pip` hosts:

* local installs use `requirements.local.txt` and `requirements.dev.txt`
* cloud installs also include `requirements.cloud.txt`

For `uv` hosts:

* the installer copies `pyproject.toml` and `uv.lock`
* the installer also persists the selected host profile in `.template-profile`
* local hosts sync `base + local + dev-local` by default
* cloud hosts sync `base + local + cloud + dev-local + dev-cloud` by default
* packaging still targets cloud runtime needs

## Windows Workflow

Windows support includes setup and maintenance helpers under `scripts/windows/`.

In standard environments, teams can use normal `make` commands when `make` is
available in `PATH`. In restricted corporate environments, the repository also
supports a PowerShell wrapper flow through `scripts/windows/run_make.ps1`.

Detailed setup and day-to-day command references live in:

* `docs/windows_setup/README.md`
* `docs/windows_setup/make_install.md`
* `docs/windows_setup/uv_install.md`
* `docs/windows_setup/make_cheatlist.md`

## AI Guidance Files

The `ai/` directory is the tracked source of truth for repository guidance:

* `ai/skills.yaml` is the authoritative skills index
* `ai/skills/` contains patterns and best practices
* `ai/context.yaml` defines AI context-generation inputs

The generated `.ai/` outputs are optional artifacts. They support AI-assisted
workflows, but they are not part of runtime execution.
