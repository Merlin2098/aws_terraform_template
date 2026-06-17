# Bash Core Patterns

## When to use

- Generating Bash scripts for Linux, WSL, or Git Bash environments
- CI/CD pipeline steps that run on Linux runners
- DevOps automation (build, deploy, validate) on POSIX systems
- Generating the Bash equivalents of PowerShell scripts (see `ai/skills/shell/environment_detection.md`)

## Required header

Every Bash script must start with:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

- `set -e` — exit immediately on error
- `set -u` — treat unset variables as errors
- `set -o pipefail` — pipeline returns failure if any command fails

## Script template

```bash
#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Script: <name>.sh
# Purpose: <one line>
# Usage: ./<name>.sh [--env dev] [--dry-run]
# ---------------------------------------------------------------------------

# ---- defaults / env vars --------------------------------------------------
ENV=${APP_ENV:-dev}
DRY_RUN=false

# ---- argument parsing -----------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --env)     ENV="$2";    shift 2 ;;
        --dry-run) DRY_RUN=true; shift  ;;
        *)         echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

# ---- functions ------------------------------------------------------------
log()  { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }
die()  { echo "ERROR: $*" >&2; exit 1; }

# ---- guards ---------------------------------------------------------------
command -v aws  >/dev/null 2>&1 || die "aws CLI not found"
[[ -n "$ENV" ]]                  || die "ENV must not be empty"

# ---- main -----------------------------------------------------------------
log "Starting in environment: $ENV"

if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY RUN — no changes will be made"
fi
```

## Variables

```bash
# Always quote variable expansions
echo "Path: $PATH"              # good
echo "File: ${FILE_NAME}"      # good — explicit boundary
echo "File: $FILE_NAME_extra"  # bad — ambiguous

# Default values
NAME=${NAME:-default}          # substitute if unset or empty
COUNT=${COUNT:?COUNT is required}  # exit with message if unset
```

## Functions

```bash
# Return values via stdout; use exit codes for success/failure
get_bucket_name() {
    local env="$1"
    echo "my-app-${env}-data"
}

BUCKET=$(get_bucket_name "$ENV")
```

## Loops

```bash
# Array loop
ENVS=(dev staging prod)
for env in "${ENVS[@]}"; do
    log "Processing: $env"
done

# Glob loop (safe with spaces)
while IFS= read -r file; do
    log "Found: $file"
done < <(find . -name '*.json' -type f)
```

## Exit codes

```bash
# Check last command explicitly
if ! aws s3 ls "s3://$BUCKET" >/dev/null 2>&1; then
    die "Bucket not accessible: $BUCKET"
fi

# Or let set -e handle it (preferred for simple cases)
aws s3 ls "s3://$BUCKET" >/dev/null
```

## Portable compatibility (Linux / WSL / Git Bash)

| Concern | Portable approach |
|---|---|
| Date formatting | `date -u +%Y-%m-%dT%H:%M:%SZ` — avoid macOS-only flags |
| `sed` | Prefer `sed -E` (POSIX ERE) over GNU-only `-r` where both work |
| `readlink -f` | Not on macOS — use `realpath` or `cd -P && pwd` |
| `stat` format | Different on Linux vs macOS — prefer Python for cross-platform stat |
| Line endings | Use `\n` only; strip `\r` from Windows-sourced files with `tr -d '\r'` |

For Git Bash on Windows, avoid `/proc/`, `mkfifo`, and `nohup` — they may not be available.

## Best practices

- Declare all constants at the top, before functions
- Use `local` for all function-scoped variables
- Redirect error messages to stderr: `echo "error" >&2`
- Validate required tools with `command -v` at script start
- Use `[[ ... ]]` (Bash conditional) rather than `[ ... ]` (POSIX sh)
- Prefer `$(...)` over backticks for command substitution

## Avoid

- Missing `set -euo pipefail` — single most common source of silent failures
- Unquoted variable expansions: `rm -rf $DIR` (dangerous if `$DIR` is empty or contains spaces)
- `exit 0` at end of script — `set -e` already handles error exits; `exit 0` is noise
- `source`-ing files without checking they exist first
- Hardcoding usernames or absolute home paths (`/home/alice/...`)

## Anti-patterns

```bash
# BAD: silent failure
aws s3 cp file.txt s3://bucket/ || true

# GOOD: explicit skip with log
if ! aws s3 cp file.txt "s3://$BUCKET/"; then
    log "WARNING: upload failed, skipping"
fi

# BAD: unquoted glob expansion
for f in $FILES; do ...

# GOOD: array
readarray -t FILES < <(find . -name '*.log')
for f in "${FILES[@]}"; do ...
```
