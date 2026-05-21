# Windows Setup

This guide prepares a Windows machine to use this template and to install it into
another repository.

Use this Windows documentation set in this order:

1. `README.md` for the general operational flow
2. [make_install.md](make_install.md) for GNU Make installation and corporate/manual usage
3. [uv_install.md](uv_install.md) for uv installation and corporate/manual usage
4. [make_cheatlist.md](make_cheatlist.md) for day-to-day `make` command examples

## Prepare the Template Repository

From the repository root:

```powershell
.\scripts\windows\setup_env.ps1
```

This Windows wrapper resolves Python automatically, validates `uv`, creates
`.venv` if needed, and syncs the local environment using the project's current
`pyproject.toml` and `uv.lock`.

By default, the local uv workflow installs:

- the shared base dependencies from `pyproject.toml`
- the `dev-local` dependency group

The cloud uv workflow installs:

- the shared base dependencies from `pyproject.toml`
- the `local` and `cloud` optional dependency sets
- the `dev-local` and `dev-cloud` dependency groups

`requirements.local.txt` and `requirements.cloud.txt` remain relevant for
pip-based hosts copied from this template. Uv-based hosts use `pyproject.toml`
and `uv.lock` instead.

When you install this template into another repository, the local profile copies
`requirements.local.txt` plus `requirements.dev.txt`. The cloud profile copies
`requirements.local.txt`, `requirements.cloud.txt`, and `requirements.dev.txt`
so a local MVP can evolve into a cloud-ready project. That requirements flow is
used only when the host chooses pip. When the host chooses uv, the installer
copies `pyproject.toml` and `uv.lock` and skips all `requirements*.txt` files.
The installer also writes `.template-profile` so the host keeps its selected uv
profile as the default for wrappers and sync commands. The installer does not
create or modify the host repository's `requirements.txt`.

Install pre-commit into the current repository environment:

```powershell
.\.venv\Scripts\pre-commit.exe install
.\.venv\Scripts\pre-commit.exe --version
```

To run all configured hooks manually:

```powershell
.\.venv\Scripts\pre-commit.exe run --all-files
```

In this template repository, the `sync-dependencies` hook defaults to `uv`
because the template itself is maintained with `pyproject.toml` and `uv.lock`.
When the installer creates a pip-based host, it rewrites that hook to use
`--manager pip` and the selected host profile instead.

Reference: https://pre-commit.com/

## Refresh or Change the Environment

To refresh the local uv environment after editing dependencies:

```powershell
.\scripts\windows\update_venv.ps1
```

To prepare the local environment with cloud dependencies explicitly:

```powershell
.\scripts\windows\update_venv.ps1 -Profile cloud
```

For uv-based hosts, the default profile comes from `.template-profile`. A local
host stays on `base + dev-local` unless you override it explicitly, and
a cloud host defaults to `base + local + cloud + dev-local + dev-cloud`.

## Use Make On Windows

If `make.exe` is not available in `PATH`, use the Windows wrapper:

```powershell
.\scripts\windows\run_make.ps1 test
.\scripts\windows\run_make.ps1 uv-init
.\scripts\windows\run_make.ps1 uv-update
```

To point at a specific `make.exe` explicitly:

```powershell
.\scripts\windows\run_make.ps1 -MakePath 'C:\custom\make.exe' test
```

For installation details and corporate/manual make resolution, see
[make_install.md](make_install.md). For ready-to-copy command examples, see
[make_cheatlist.md](make_cheatlist.md).

## uv Installation and Validation

For uv installation paths, corporate/manual workflows, and the package refresh
warning for uv-based hosts, see [uv_install.md](uv_install.md).

## Install This Template Into Another Repo

Preview the install without writing files:

```powershell
.\.venv\Scripts\python.exe install_windows.py --dry-run --target C:\path\to\target-repo
```

Install the template by selecting the target repository folder in Explorer:

```powershell
.\.venv\Scripts\python.exe install_windows.py
```

Install the template with an explicit target path:

```powershell
.\.venv\Scripts\python.exe install_windows.py --target C:\path\to\target-repo
```

Install and choose the package manager non-interactively:

```powershell
.\.venv\Scripts\python.exe install_windows.py --target C:\path\to\target-repo --local --pip
.\.venv\Scripts\python.exe install_windows.py --target C:\path\to\target-repo --cloud --uv
```

Overwrite existing target files only when intentional:

```powershell
.\.venv\Scripts\python.exe install_windows.py --target C:\path\to\target-repo --force
```

If the target repository already has a `.gitignore`, the installer keeps that
file and appends only the ignore rules that are present in the template
`.gitignore` but missing in the host. If the target repository does not have a
`.gitignore`, the template `.gitignore` is copied as-is.

The installer does not run Terraform, install dependencies, initialize Git, or
execute pre-commit in the target repository.

The installer also leaves the installer entrypoints and template docs behind:
`install_windows.py`, `install_linux.py`, files named `README.md`, and `docs/`
are not copied to the target repository.

## How the Host Setup Works

When the target host chooses `pip`:

- the installer copies `requirements.local.txt` and `requirements.dev.txt`
- for cloud pip hosts, it also copies `requirements.cloud.txt`
- the host hook is rewritten to run `sync_dependencies.py --manager pip --profile <selected-profile>`
- the `Makefile` is rendered for pip-based dependency sync

When the target host chooses `uv`:

- the installer copies `pyproject.toml` and `uv.lock`
- it writes `.template-profile` with the selected host profile
- it skips all `requirements*.txt` files
- the host hook keeps the template `uv` behavior
- the `Makefile` uses the persisted profile by default
- local hosts default to `base + dev-local`
- cloud hosts default to `base + local + cloud + dev-local + dev-cloud`

For uv-based hosts, packaging for deployment still uses the cloud dependency set
from `pyproject.toml` and `uv.lock`, even if the local development environment
remains on the default local profile.
