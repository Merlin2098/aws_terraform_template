# Template Versioning and Host Updates

This guide explains how the installer detects whether a host repository needs
updating, how to force a reinstall during development, and when to switch to
proper version bumps.

## How Version Detection Works

Every installation writes a `.framework-version.json` file to the host
repository root. It records the template version at the time of install:

```json
{
  "framework_version": "0.1.0",
  "installed_at": "...",
  "include_structure": false,
  "enabled_capabilities": [...],
  "framework_manifest": [...]
}
```

When you run the installer against an already-installed host, `update_template`
in `ai/installer.py` compares `framework_version` in that file against the
`version` field in the template's `pyproject.toml`. If they match, the update
is skipped entirely:

```python
if previous_version == current_version and not force:
    return {"up_to_date": True, ...}
```

This means **changing files in the template without bumping the version will
not propagate to the host** — the installer considers it already current.

## Current Workaround: --force

Pass `--force` to bypass the version check and overwrite all framework-owned
files regardless of version:

```powershell
python install_windows.py --target <path-to-host> --force
```

Use `--dry-run --force` first to preview what would be written without touching
anything:

```powershell
python install_windows.py --target <path-to-host> --force --dry-run
```

`--force` is safe for iterative development but should not become the default
workflow in production — it makes update history invisible.

## When to Switch to Version Bumps

Switch to bumping `pyproject.toml` when any of these apply:

- The template is shared across more than one host repository
- You want a clear audit trail of what version a host is running
- You are introducing a breaking change to framework-owned files
- CI/CD automation needs to detect out-of-date hosts reliably

## How to Bump the Version

Open `pyproject.toml` and increment `version` following
[Semantic Versioning](https://semver.org/):

| Change type | Example bump |
|---|---|
| Patch — small fix or content update | `0.1.0` → `0.1.1` |
| Minor — new capability or file added | `0.1.0` → `0.2.0` |
| Major — breaking change to structure | `0.1.0` → `1.0.0` |

After bumping, run the installer normally (no `--force` needed):

```powershell
python install_windows.py --target <path-to-host>
```

The installer will detect `previous_version != current_version`, copy all
framework-owned files, and update `.framework-version.json` in the host.

## Quick Reference

| Goal | Command |
|---|---|
| Force update, skip version check | `python install_windows.py --target <path> --force` |
| Preview force update (no writes) | `python install_windows.py --target <path> --force --dry-run` |
| Normal update after version bump | `python install_windows.py --target <path>` |
| Check current template version | `grep ^version pyproject.toml` |
| Check host installed version | `cat <host>/.framework-version.json` |
