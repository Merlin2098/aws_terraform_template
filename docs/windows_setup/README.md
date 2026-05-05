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
- the `local` optional dependency set
- the `dev` dependency group

`requirements.local.txt` and `requirements.cloud.txt` remain relevant for
pip-based hosts copied from this template. Uv-based hosts use `pyproject.toml`
and `uv.lock` instead.

When you install this template into another repository, the local profile copies
`requirements.local.txt` plus `requirements.dev.txt`. The cloud profile copies
`requirements.local.txt`, `requirements.cloud.txt`, and `requirements.dev.txt`
so a local MVP can evolve into a cloud-ready project. That requirements flow is
used only when the host chooses pip. When the host chooses uv, the installer
copies `pyproject.toml` and `uv.lock` and skips all `requirements*.txt` files.
The installer does not create or modify the host repository's `requirements.txt`.

Install pre-commit into the current repository environment:

```powershell
.\.venv\Scripts\pre-commit.exe install
.\.venv\Scripts\pre-commit.exe --version
```

To run all configured hooks manually:

```powershell
.\.venv\Scripts\pre-commit.exe run --all-files
```

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

Cloud is an explicit step for uv-based Windows hosts. The normal local
development path remains `base + local + dev`.

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

The installer copies template files into the target repository and adds these
entries to the target `.gitignore` if they are missing:

```gitignore
ai/
.ai/
data/
AGENTS.md
Makefile
```

The installer does not run Terraform, install dependencies, initialize Git, or
execute pre-commit in the target repository.

The installer also leaves the installer entrypoints and template docs behind:
`install_windows.py`, `install_linux.py`, files named `README.md`, and `docs/`
are not copied to the target repository.

## How the Host Setup Works

When the target host chooses `pip`:

- the installer copies `requirements.local.txt` and `requirements.dev.txt`
- for cloud pip hosts, it also copies `requirements.cloud.txt`
- the host hook and `Makefile` are rendered for pip-based dependency sync

When the target host chooses `uv`:

- the installer copies `pyproject.toml` and `uv.lock`
- it skips all `requirements*.txt` files
- the host hook and `Makefile` are rendered for a stable local uv workflow
- cloud remains an explicit environment update step, not the default sync mode

For uv-based hosts, packaging for deployment still uses the cloud dependency set
from `pyproject.toml` and `uv.lock`, even if the local development environment
remains on the default local profile.
