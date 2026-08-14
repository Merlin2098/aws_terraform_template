# Install uv on Windows

Use this guide when you need a clear Windows setup path for uv in one of these
two modes:

- uv available normally in `PATH`
- uv managed through an approved corporate or manual installation path

This guide is intentionally split into `PATH` and corporate/manual flows so the
operational difference stays explicit.

## 1. uv When It Is Available in PATH

Use this path when `uv` is already installed normally and can be called
directly.

Verify (Git Bash):

```bash
uv --version
which uv
```

Typical usage:

```bash
uv sync --group dev-local
uv lock
uv tree
```

This is the simplest path for local developer machines. PowerShell fallback:
`Get-Command uv` in place of `which uv` — the rest of the commands are
identical in both shells.

Reference: https://docs.astral.sh/uv/getting-started/installation/

## 2. uv In Corporate or Restricted Environments

Use this path when:

- the approved `uv` installation is not in `PATH`
- the standalone installer is blocked
- you need an explicit, supportable command path

Before choosing one of the options below, verify what Python entrypoint is
available on the machine. In Git Bash, `py` and `python` are the same Windows
launchers on `PATH` as in PowerShell — no translation needed:

```bash
py -3 --version
python -V
py -0p
test -f '/c/Program Files/Python314/python.exe' && echo found
```

PowerShell equivalent for the last check: `Test-Path 'C:\Program
Files\Python314\python.exe'`. You do not need every command above to succeed
— the goal is to confirm which approved Python path or launcher is actually
available in your environment.

### Option A: Use Python to Run uv

If Python is available but `uv` is not exposed as a standalone command:

```bash
py -3 -m uv --version
```

If that works, you can operate uv through Python:

```bash
py -3 -m uv sync --group dev-local
py -3 -m uv tree
```

This is the preferred corporate path when Python is the approved entrypoint.

If you want one reusable pattern for support and diagnostics, keep the command
explicit and consistent. Git Bash:

```bash
'/c/Program Files/Python314/python.exe' -m uv --version
'/c/Program Files/Python314/python.exe' -m uv sync --group dev-local
'/c/Program Files/Python314/python.exe' -m uv tree
```

PowerShell fallback: prefix each call with `&` and use backslash paths
(`& 'C:\Program Files\Python314\python.exe' -m uv --version`).

### Option B: Use an Approved Corporate uv Binary

If your company distributes a dedicated `uv.exe`, verify it directly:

```bash
/c/approved-tools/uv/uv.exe --version
```

Then use it explicitly:

```bash
/c/approved-tools/uv/uv.exe sync --extra local --group dev
/c/approved-tools/uv/uv.exe tree
```

### Option C: Install uv Through an Approved Python

If the approved flow is to install `uv` via Python rather than as a standalone
binary:

```bash
'/c/Program Files/Python314/python.exe' -m pip install uv
'/c/Program Files/Python314/python.exe' -m uv --version
```

After that, continue to run uv through the same Python:

```bash
'/c/Program Files/Python314/python.exe' -m uv sync --group dev-local
```

This keeps the execution path explicit and avoids depending on `PATH` changes or
on a separately installed `uv.exe`. PowerShell fallback: same arguments with
`& 'C:\Program Files\Python314\python.exe'` and backslash paths.

## 3. How This Repository Uses uv

The repository scripts assume uv is available through one of the paths above
and then use it to drive the local environment.

Primary commands (Git Bash):

```bash
./scripts/linux/setup_env.sh
./scripts/linux/update_venv.sh
```

PowerShell fallback:

```powershell
.\scripts\windows\setup_env.ps1
.\scripts\windows\update_venv.ps1
```

Behavior:

- `setup_env.ps1` resolves Python automatically, validates uv, creates `.venv`
  if needed, and syncs the local environment
- `update_venv.ps1` refreshes the environment after dependency changes
- both wrappers prefer `python -m uv` for the selected interpreter and fall
  back to `uv.exe` from `PATH` when that is the only valid local installation
- active capabilities determine all extras and dependency groups
- active host capabilities are read from `.template-profile.yaml`
- cloud capabilities can be enabled in `.template-profile.yaml` and then
  synchronized by re-running `./scripts/linux/update_venv.sh` (or the
  PowerShell fallback `.\scripts\windows\update_venv.ps1`)

## 4. Uv Host Package Refresh Warning

Some Windows hosts or VS Code extensions inspect the active environment with
`python -m pip list` or similar `pip`-based commands when they refresh the
package view.

For uv-based hosts, that refresh can show a warning such as
`error refreshing packages` even when the project environment is healthy and
`uv sync` completed successfully.

Treat this as a host-tooling limitation first, not as proof that dependency
installation failed.

When validating a uv-based host, prefer these checks (Git Bash — identical in
PowerShell aside from the path separator):

```bash
py -3 -m uv sync --group dev-local
py -3 -m uv tree
py -3 -m uv pip list --python ./.venv/Scripts/python.exe
```

If those commands work and the project dependencies import correctly, the
environment is generally usable even if the host package view still shows a
refresh warning.

If the host must refresh packages through `pip`, enable `pip` inside the
project virtual environment as an optional compatibility workaround:

```bash
./.venv/Scripts/python.exe -m ensurepip --upgrade
./.venv/Scripts/python.exe -m pip list
```

Do not treat this step as part of the default uv workflow. Use it only when the
host tooling requires `pip` for package inspection.

## 5. Quick Verification Commands

Git Bash:

```bash
uv --version
py -3 -m uv --version
./scripts/linux/setup_env.sh
./scripts/linux/update_venv.sh
```

PowerShell fallback: same commands with `.\scripts\windows\setup_env.ps1` and
`.\scripts\windows\update_venv.ps1`.

Replace `C:\Program Files\Python314\python.exe` (or its Git Bash form,
`/c/Program Files/Python314/python.exe`) with the real approved Python path on
the machine whenever you use the explicit Python-driven examples above.
