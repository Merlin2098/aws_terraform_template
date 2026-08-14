# Template Versioning and Host Updates

This guide explains how the installer detects whether a host repository needs
updating, how divergence is classified, and when to bump the framework version.

## How Divergence Detection Works

Every installation writes a `.framework-version.json` file to the host
repository root. It records the template version, the installed capability set,
and **content fingerprints** for every framework-owned file:

```json
{
  "framework_version": "0.2.0",
  "installed_at": "...",
  "include_structure": false,
  "enabled_capabilities": ["languages:python"],
  "tree_digest": "a3f8…",
  "framework_manifest": {
    "AGENTS.md":              {"sha256": "b1c2…", "ownership": "managed"},
    "ai/policies/global.md":  {"sha256": "d4e5…", "ownership": "managed"},
    "…": {}
  }
}
```

`tree_digest` is an aggregate hash of the entire framework-owned tree (all
`sha256` values, sorted by path). When you run the installer against an
already-installed host, `update_template` uses it as a fast gate:

```python
if template_tree_digest == state["tree_digest"] and not locally_modified:
    return {"up_to_date": True, ...}
```

If the tree matches **and** no file in the host was locally modified, the update
is skipped immediately without reading every file.

### Three-way classification

When the tree has changed (or `--force` is passed), each framework-owned file
is classified by comparing three hashes:

| Host file vs state hash | Template vs state hash | Classification | Action |
|---|---|---|---|
| same | same | `unchanged` | nothing |
| same | different | `updatable` | overwrite |
| different | same | `locally-modified` | preserve + warn |
| different | different | `conflict` | preserve + warn |
| missing | — | `missing` | re-copy |

`--force` bypasses the classification and overwrites all `managed` files.

### Ownership

Each manifest entry carries an `ownership` value:

| Value | Meaning |
|---|---|
| `managed` | Framework owns this file; overwritten on every update. |
| `generated` | Rendered at install time (e.g. `.template-profile.yaml`); hash is of the rendered output. |

`src/`, `infra/`, `tests/`, and `specs/project/` are **host-owned** and never
appear in the manifest — the installer never touches them.

## Role of `framework_version`

`framework_version` is a **governance label** (changelog, breaking-change
anchor), not a sync detector. Changing files in the template without bumping the
version **will still propagate** to the host — the divergence detector is the
tree digest and per-file hashes, not the version string.

Use `framework_version` to:

- Communicate what a host is running (e.g. `0.2.0`).
- Anchor breaking changes that require a forced reinstall.
- Build a changelog across releases.

## Workarounds

### `--force`: bypass classification

Pass `--force` to overwrite all `managed`/`generated` files regardless of
their classification:

```bash
python install.py --target <path-to-host> --force
```

Use `--dry-run --force` first to preview what would be written:

```bash
python install.py --target <path-to-host> --force --dry-run
```

(These commands are identical in Git Bash and PowerShell.)

### Handling `locally-modified` / `conflict`

If the update reports locally-modified or conflicting files, review the
differences manually and then re-run with `--force` to accept the template
version, or keep your edits as-is.

## When to Bump the Version

Bump `pyproject.toml` `version` when:

- You want a clear audit trail of what generation a host is running.
- You are introducing a breaking change that requires re-running the installer.
- CI/CD automation needs to report the running generation.

Version bumps follow [Semantic Versioning](https://semver.org/):

| Change type | Example bump |
|---|---|
| Patch — small fix or content update | `0.1.0` → `0.1.1` |
| Minor — new capability or file added | `0.1.0` → `0.2.0` |
| Major — breaking change to structure | `0.1.0` → `1.0.0` |

After bumping, run the installer normally — the divergence detector will find
the changed files regardless:

```bash
python install.py --target <path-to-host>
```

## Quick Reference

| Goal | Command |
|---|---|
| Update host (smart diff) | `python install.py --target <path>` |
| Force overwrite all framework files | `python install.py --target <path> --force` |
| Preview update (no writes) | `python install.py --target <path> --dry-run` |
| Preview force update | `python install.py --target <path> --force --dry-run` |
| Check current template version | `grep ^version pyproject.toml` |
| Check host installed version | `cat <host>/.framework-version.json` |

## Architecture reference

The fingerprint mechanism is specified in
[`specs/rework/ADR-FW-003.md`](../../../specs/rework/ADR-FW-003.md) and
analysed in
[`specs/rework/SPEC-FW-016.md`](../../../specs/rework/SPEC-FW-016.md).
