# Windows Setup

This guide prepares a Windows machine to use this template and to install it into
another repository.

Start with [tools.md](tools.md) to install GNU Make, uv, and the supporting
command-line tools. It includes both admin and no-admin paths for restricted
corporate machines.

## Prepare Python and Pre-commit

From the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.local.txt -r requirements.dev.txt
.\.venv\Scripts\pre-commit.exe install
```

`requirements.local.txt` installs the local developer environment. Deployment
bundles use `requirements.cloud.txt` during packaging for pip-based hosts.
Uv-based hosts use `pyproject.toml` and `uv.lock` instead.

When you install this template into another repository, the local profile copies
`requirements.local.txt` plus `requirements.dev.txt`. The cloud profile copies
`requirements.local.txt`, `requirements.cloud.txt`, and `requirements.dev.txt`
so a local MVP can evolve into a cloud-ready project. That requirements flow is
used only when the host chooses pip. When the host chooses uv, the installer
copies `pyproject.toml` and `uv.lock` and skips all `requirements*.txt` files.
The installer does not create or modify the host repository's `requirements.txt`.

Verify pre-commit:

```powershell
.\.venv\Scripts\pre-commit.exe --version
```

To run all configured hooks manually:

```powershell
.\.venv\Scripts\pre-commit.exe run --all-files
```

Reference: https://pre-commit.com/

## Uv Host Package Refresh Warning

Some Windows hosts or VS Code extensions inspect the active environment with
`python -m pip list` or similar `pip`-based commands when they refresh the
package view.

For uv-based hosts, that refresh can show a warning such as
`error refreshing packages` even when the project environment is healthy and
`uv sync` completed successfully.

Treat this as a host-tooling limitation first, not as proof that dependency
installation failed.

When validating a uv-based host, prefer these checks:

```powershell
uv sync --extra local
uv tree
uv pip list --python .\.venv\Scripts\python.exe
```

If those commands work and the project dependencies import correctly, the
environment is generally usable even if the host package view still shows a
refresh warning.

If the host must refresh packages through `pip`, enable `pip` inside the
project virtual environment as an optional compatibility workaround:

```powershell
.\.venv\Scripts\python.exe -m ensurepip --upgrade
.\.venv\Scripts\python.exe -m pip list
```

Do not treat this step as part of the default uv workflow. Use it only when the
host tooling requires `pip` for package inspection.

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
