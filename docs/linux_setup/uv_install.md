# Install uv on Linux

Use this guide when you need a clear Linux setup path for uv in one of these
two modes:

- uv available normally in `PATH`
- uv managed through an approved manual or corporate installation path

Examples target Ubuntu and similar distributions, but the workflow stays
generic: validate the available Python entrypoint, then validate `uv`.

## 1. uv When It Is Available in PATH

Use this path when `uv` is already installed normally and can be called
directly.

Verify:

```bash
uv --version
command -v uv
```

Typical usage:

```bash
uv sync --group dev-local
uv lock
uv tree
```

Reference: https://docs.astral.sh/uv/getting-started/installation/

## 2. uv In Manual or Corporate Environments

Use this path when:

- the approved `uv` installation is not in `PATH`
- the installer is blocked
- you need an explicit, supportable command path

Before choosing one of the options below, verify what Python entrypoint is
available on the machine:

```bash
command -v python3
python3 --version
command -v python
python --version
ls /usr/bin/python3
```

You do not need every command above to succeed. The goal is to confirm which
approved Python path is actually available in your environment.

### Option A: Use Python to Run uv

If Python is available but `uv` is not exposed as a standalone command:

```bash
python3 -m uv --version
```

If that works, you can operate uv through Python:

```bash
python3 -m uv sync --group dev-local
python3 -m uv tree
```

This is the preferred manual path when Python is the approved entrypoint.

### Option B: Use an Approved Corporate uv Binary

If your company distributes a dedicated `uv` binary, verify it directly:

```bash
/opt/company-tools/uv --version
```

Then use it explicitly:

```bash
/opt/company-tools/uv sync --group dev-local
/opt/company-tools/uv tree
```

## 3. How This Repository Uses uv

Primary commands:

```bash
./scripts/linux/setup_env.sh
./scripts/linux/update_venv.sh
```

Behavior:

- `setup_env.sh` resolves Python automatically, validates uv, and syncs the
  local environment
- `update_venv.sh` refreshes the environment after dependency changes
- both wrappers prefer `python -m uv` for the selected interpreter and fall
  back to `uv` from `PATH` when that is the only valid local installation
- the normal local uv workflow is `base + dev-local`
- cloud hosts default to `base + local + cloud + dev-local + dev-cloud`
- the active host capabilities are read from `.template-profile.yaml`

To force the cloud profile explicitly:

```bash
# Enable infrastructure:terraform in .template-profile.yaml, then:
./scripts/linux/update_venv.sh
```

To sync only runtime dependencies:

```bash
./scripts/linux/setup_env.sh --no-dev
```

## 4. Quick Verification Commands

```bash
uv --version
python3 -m uv --version
./scripts/linux/setup_env.sh
./scripts/linux/update_venv.sh
```
