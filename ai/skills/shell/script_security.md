# Script Security

## When to use

- Before generating any script that contains destructive commands
- When reviewing an existing script for safety
- When a user asks to automate operations that delete, overwrite, or deploy

## Destructive operations that require explicit confirmation

Flag these patterns and require user acknowledgement before generating or running them:

### Bash

```bash
rm -rf "$DIR"                          # recursive force delete
find . -delete                         # delete all found files
> /etc/someconfig                      # truncate system file
dd if=/dev/zero of=/dev/sdX            # disk wipe
mkfs.*                                 # format filesystem
terraform destroy                      # destroy all infra
aws s3 rb s3://bucket --force          # delete bucket and contents
```

### PowerShell

```powershell
Remove-Item -Recurse -Force $Path      # recursive force delete
Format-Volume                          # disk format
terraform destroy                      # destroy all infra
aws s3 rb s3://bucket --force          # delete bucket and contents
```

## Required: ShouldProcess guard (PowerShell)

Every PowerShell function that deletes, overwrites, or modifies system state must use `SupportsShouldProcess`:

```powershell
[CmdletBinding(SupportsShouldProcess)]
param([string]$Path)

if ($PSCmdlet.ShouldProcess($Path, 'Remove-Item -Recurse -Force')) {
    Remove-Item -Recurse -Force $Path
}
```

## Required: dry-run mode (Bash)

Every Bash script with destructive operations should support `--dry-run`:

```bash
DRY_RUN=false
while [[ $# -gt 0 ]]; do
    case "$1" in --dry-run) DRY_RUN=true; shift ;; *) shift ;; esac
done

execute() {
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "[DRY RUN] would run: $*"
    else
        "$@"
    fi
}

execute rm -rf "$STALE_DIR"
```

## Required: confirmation prompt for irreversible operations

For operations that cannot be undone (drop database, delete S3 bucket, terraform destroy):

```bash
read -r -p "This will permanently delete $RESOURCE. Type 'yes' to confirm: " CONFIRM
[[ "$CONFIRM" == "yes" ]] || { echo "Aborted."; exit 0; }
```

```powershell
$confirm = Read-Host "This will permanently delete $Resource. Type 'yes' to confirm"
if ($confirm -ne 'yes') { Write-Warning "Aborted."; return }
```

## Secret hygiene

- Never include credentials, tokens, or passwords in script text
- Use environment variables (`$env:AWS_ACCESS_KEY_ID`, `$AWS_SECRET_ACCESS_KEY`) — read at runtime, never hardcoded
- Never log secrets, even in debug/verbose output
- Reject scripts that contain inline secrets; generate a pattern that reads from env vars instead

```bash
# BAD
aws configure set aws_secret_access_key AKIA123...

# GOOD — read from environment
: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID must be set}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY must be set}"
```

## Approval boundaries (AGENTS.md alignment)

The following operations always require explicit user approval, regardless of script context:

| Operation | Reason |
|---|---|
| `terraform apply` | Modifies production infrastructure state |
| `terraform destroy` | Irreversible destruction of infrastructure |
| Overwrite data or generated artifacts | User-owned data at risk |

These mirror the AGENTS.md "Never without approval" list and must be enforced even in fully automated scripts.

## Avoid

- Generating scripts with `rm -rf` or `Remove-Item -Recurse -Force` without a `ShouldProcess` / `--dry-run` guard
- Inline credentials or secrets of any kind
- Silent error suppression (`|| true`, `-ErrorAction SilentlyContinue`) on destructive operations
- Chaining destructive operations without intermediate validation steps
- Executing unvalidated user input directly in shell commands (injection risk)

## Anti-patterns

```bash
# DANGEROUS: path injection
TARGET_DIR="$1"
rm -rf "$TARGET_DIR"   # if $1 is empty or /, catastrophic

# SAFE
TARGET_DIR="${1:?must provide target directory}"
[[ "$TARGET_DIR" == /* ]] && die "absolute paths not allowed"
rm -rf "$TARGET_DIR"
```
