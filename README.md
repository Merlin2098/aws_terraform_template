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
* how project contracts (specs) should be separated from patterns (skills) and hard rules (principles)

This template solves that by giving you a consistent installation path and a
simple operational model that can be copied into a host repository.

## Current Status

The template currently supports:

* installation into another repository through Windows and Linux installer entrypoints
* host setup for either `pip` or `uv`
* `local` and `cloud` dependency profiles
* optional copying of `src/`, `infra/`, and `tests/`
* a `specs/` layer for project contracts, cloud-profile only, with a clear separation between template-owned specs (`specs/template/`) and host-authored specs (`specs/project/`)
* an opt-in remote Terraform backend example using S3 native locking (no DynamoDB)
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
specs/                 Project contracts (cloud profile only)
  specs/template/      Template-owned contracts — read-only in host repos
  specs/project/       Host-authored contracts — written by the host project
tests/                 Lightweight validation
```

## Common Commands

```bash
make package
make test
make ai-refresh
./scripts/linux/setup_env.sh
./scripts/linux/update_venv.sh
./scripts/windows/setup_env.ps1
./scripts/windows/update_venv.ps1
./scripts/windows/run_make.ps1 test
python3 scripts/hooks/ai_refresh.py
python install_windows.py --target /path/to/repo --dry-run
python3 install_linux.py --target /path/to/repo --dry-run
terraform -chdir=infra init
terraform -chdir=infra plan
```

For Linux setup, including Ubuntu-style `uv` and `make` usage, see
`docs/linux_setup/`. For Windows-specific `make` usage, including corporate
environments where `make.exe` is not in `PATH`, see `docs/windows_setup/`.

For Terraform design guardrails used by this template and intended host
repositories, see `docs/terra_principles.md`.

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

Use `install_linux.py` or `install_windows.py` only to copy the template into a
host repository. To bootstrap the current repository environment, use the OS
setup wrappers under `scripts/linux/` or `scripts/windows/`.

## Dependency Model

The template supports two host dependency workflows.

For `pip` hosts:

* local installs use `requirements.local.txt` and `requirements.dev.txt`
* cloud installs also include `requirements.cloud.txt`
* the installer rewrites the `sync-dependencies` hook to run with `--manager pip` and the selected profile

For `uv` hosts:

* the installer copies `pyproject.toml` and `uv.lock`
* the installer also persists the selected host profile in `.template-profile`
* the `sync-dependencies` hook keeps the template's `uv` default
* local hosts sync `base + dev-local` by default
* cloud hosts sync `base + local + cloud + dev-local + dev-cloud` by default
* packaging still targets cloud runtime needs, even when local development stays on the lighter local profile

## Linux Workflow

Linux support includes setup and maintenance helpers under `scripts/linux/`.

On Ubuntu and similar distributions, native `make` is the standard path and the
repository provides explicit shell wrappers for uv environment setup:

* `./scripts/linux/setup_env.sh`
* `./scripts/linux/update_venv.sh`
* `make uv-init`
* `make uv-update`
* `make test`

Detailed setup and day-to-day command references live in:

* `docs/linux_setup/README.md`
* `docs/linux_setup/uv_install.md`
* `docs/linux_setup/make_cheatlist.md`

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

## Project Contracts (specs/)

The `specs/` directory holds project contracts: short, durable documents that
state what is true, expected, or invariant about the project. Contracts
complement skills (patterns) and principles (hard rules) without overlapping
them.

`specs/` is only present in **cloud-profile** installations. Local-profile
hosts do not receive this folder.

The folder is split into two areas:

* `specs/template/` — contracts inherited from the template. Read-only in host
  repos; refresh by re-running the installer.
* `specs/project/` — empty placeholder in the template. The host project writes
  its own contracts here, following the format defined in
  `specs/template/000-template-spec-format.md`.

Template specs cover the template contract, the `infra/` baseline invariants,
and how the guidance layers (skills, specs, principles) relate to each other.

## Remote Terraform Backend

By default, Terraform uses a local backend for dev and sandbox work. When you
need to share state across users or CI, the template ships an opt-in example:

```bash
cp infra/backend.tf.example infra/backend.tf
# edit bucket, key, and region, then:
terraform -chdir=infra init
```

The example uses **S3 native locking** (`use_lockfile = true`) introduced in
Terraform 1.10 and AWS provider 5.81. No DynamoDB table is required. The state
bucket should have versioning enabled and `force_destroy = false`.

`backend.tf` is gitignored (host-specific). `backend.tf.example` is versioned
and safe to commit.
