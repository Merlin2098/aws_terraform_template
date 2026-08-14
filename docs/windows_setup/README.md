# Windows Setup

This guide prepares a Windows machine to use this template and to install it into
another repository.

**Git Bash is the primary shell on Windows.** All core commands below run
identically in Git Bash and in a native Linux/WSL shell — `make`, `uv`, and the
`scripts/linux/*.sh` wrappers work as-is once `make.exe` and Python are on
`PATH` (see [make_install.md](make_install.md)). PowerShell remains a fully
supported **fallback** for Windows-only needs: no `make.exe`/POSIX shell
available, corporate-locked environments, or scripts that must touch Windows
services, the registry, or scheduled tasks. Every PowerShell command in this
set has a Git Bash equivalent shown alongside it.

Use this Windows documentation set in this order:

1. `README.md` for the general operational flow
2. [make_install.md](make_install.md) for GNU Make installation and corporate/manual usage
3. [uv_install.md](uv_install.md) for uv installation and corporate/manual usage
4. [make_cheatlist.md](make_cheatlist.md) for day-to-day `make` command examples
5. [template_versioning.md](template_versioning.md) for how version detection works and when to use `--force` vs version bumps

## Prepare the Template Repository

From the repository root, in Git Bash:

```bash
./scripts/linux/setup_env.sh
```

PowerShell fallback (identical behavior):

```powershell
.\scripts\windows\setup_env.ps1
```

This wrapper resolves Python automatically, validates `uv`, creates `.venv` if
needed, and syncs the local environment using the project's current
`pyproject.toml` and `uv.lock`.

By default, the local uv workflow installs:

- the shared base dependencies from `pyproject.toml`
- the `dev-local` dependency group

The cloud uv workflow installs:

- the shared base dependencies from `pyproject.toml`
- the `local` and `cloud` optional dependency sets
- the `dev-local` and `dev-cloud` dependency groups

When you install this template into another repository, the installer copies
`pyproject.toml` and `uv.lock`. The installer also writes
`.template-profile.yaml` so wrappers and sync commands use the selected
capabilities.

Install pre-commit into the current repository environment:

```bash
./.venv/Scripts/pre-commit.exe install
./.venv/Scripts/pre-commit.exe --version
```

To run all configured hooks manually:

```bash
./.venv/Scripts/pre-commit.exe run --all-files
```

PowerShell fallback:

```powershell
.\.venv\Scripts\pre-commit.exe install
.\.venv\Scripts\pre-commit.exe run --all-files
```

In this template repository, the `sync-dependencies` hook uses `uv` because the
template itself is maintained with `pyproject.toml` and `uv.lock`.

Reference: https://pre-commit.com/

## Refresh or Change the Environment

To refresh the local uv environment after editing dependencies:

```bash
./scripts/linux/update_venv.sh
```

PowerShell fallback:

```powershell
.\scripts\windows\update_venv.ps1
```

To enable cloud dependencies, set
`capabilities.infrastructure.terraform.enabled: true` in
`.template-profile.yaml`, then run the same command again.

For uv-based hosts, `.template-profile.yaml` is the active manifest. Enable or
disable capabilities there, then run `update_venv.ps1`; transitive capability
dependencies determine the extras and groups synchronized by uv.

## Use Make On Windows

With `make.exe` on `PATH` (see [make_install.md](make_install.md)), Git Bash
runs `make` directly like any POSIX shell — no wrapper needed:

```bash
make test
make uv-init
make uv-update
```

If `make.exe` is not on `PATH` and you are in PowerShell without a POSIX
shell available, use the Windows wrapper instead:

```powershell
.\scripts\windows\run_make.ps1 test
.\scripts\windows\run_make.ps1 uv-init
.\scripts\windows\run_make.ps1 uv-update
```

To point at a specific `make.exe` explicitly (PowerShell wrapper only):

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

```bash
./.venv/Scripts/python.exe install.py --dry-run --target /c/path/to/target-repo
```

Install the template with a CLI prompt for the target path:

```bash
./.venv/Scripts/python.exe install.py
```

Or open a folder picker (requires a display / Tkinter) with
`--select-target`:

```bash
./.venv/Scripts/python.exe install.py --select-target
```

Install the template with an explicit target path:

```bash
./.venv/Scripts/python.exe install.py --target /c/path/to/target-repo
```

Install and choose capabilities non-interactively:

```bash
./.venv/Scripts/python.exe install.py --target /c/path/to/target-repo --enable languages:python
./.venv/Scripts/python.exe install.py --target /c/path/to/target-repo --enable infrastructure:terraform
./.venv/Scripts/python.exe install.py --target /c/path/to/target-repo --enable none
```

Overwrite existing target files only when intentional:

```bash
./.venv/Scripts/python.exe install.py --target /c/path/to/target-repo --force
```

PowerShell fallback: use the same arguments with `.\.venv\Scripts\python.exe`
and a `C:\path\to\target-repo`-style path.

If the target repository already has a `.gitignore`, the installer keeps that
file and appends only the ignore rules that are present in the template
`.gitignore` but missing in the host. If the target repository does not have a
`.gitignore`, the template `.gitignore` is copied as-is.

The installer does not run Terraform, install dependencies, initialize Git, or
execute pre-commit in the target repository.

The installer also leaves the installer entrypoint and template docs behind:
`install.py`, files named `README.md`, and `docs/` are not copied to the
target repository.

## How the Host Setup Works

The installer:

- copies `pyproject.toml` and `uv.lock`
- writes `.template-profile.yaml` with the complete capability catalog
- keeps the template `uv` hook behavior
- renders the `Makefile` to use the persisted capabilities by default
- active capabilities determine all extras and dependency groups

Packaging resolves runtime extras from the capabilities enabled in
`.template-profile.yaml`.
