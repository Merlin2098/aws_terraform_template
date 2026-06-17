# PowerShell Filesystem Operations

## When to use

- Generating scripts that copy, move, delete, rename, compress, or expand files/directories
- Any destructive filesystem operation (delete, overwrite, compress-over-existing)
- Bulk file operations that need a dry-run mode before execution

## Key cmdlets

| Operation | Cmdlet | Notes |
|---|---|---|
| Copy | `Copy-Item` | Use `-Recurse` for directories; `-Force` only when documented |
| Move | `Move-Item` | Atomic rename within same drive |
| Delete | `Remove-Item` | **Always `-WhatIf` support required** (see below) |
| Rename | `Rename-Item` | Single item; `Move-Item` for bulk renames |
| Compress | `Compress-Archive` | Built-in; no external dependency |
| Expand | `Expand-Archive` | Use `-Force` only when overwrite is intentional |
| Test existence | `Test-Path` | Prefer over try/catch for existence checks |
| Ensure directory | `New-Item -ItemType Directory -Force` | Idempotent |

## Required: -WhatIf support on all destructive operations

Every function that deletes, overwrites, or moves files **must** support `-WhatIf`:

```powershell
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)][string]$Path,
    [switch]$Recurse
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Path)) {
    Write-Error "Path not found: $Path"
    return
}

if ($PSCmdlet.ShouldProcess($Path, 'Remove-Item')) {
    Remove-Item -Path $Path -Recurse:$Recurse -Force
    Write-Verbose "Removed: $Path"
}
```

Callers can then run with `-WhatIf` to preview without side effects:

```powershell
.\cleanup.ps1 -Path C:\Temp\old-logs -Recurse -WhatIf
```

## Idempotent patterns

```powershell
# Create directory only if it doesn't exist
New-Item -ItemType Directory -Path $Dest -Force | Out-Null

# Copy only if source is newer
if (-not (Test-Path $Dest) -or (Get-Item $Src).LastWriteTime -gt (Get-Item $Dest).LastWriteTime) {
    Copy-Item -Path $Src -Destination $Dest -Force
}
```

## Compression

```powershell
# Compress with timestamp to avoid overwrite collision
$archive = "backup-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"
Compress-Archive -Path $SourceDir -DestinationPath $archive

# Expand — confirm destination before -Force
if (Test-Path $Dest) {
    Write-Warning "Destination exists; use -Force to overwrite: $Dest"
}
Expand-Archive -Path $ZipFile -DestinationPath $Dest
```

## Best practices

- Test path existence with `Test-Path` before every operation
- Use `-WhatIf` guard on every destructive function (enforced by `[CmdletBinding(SupportsShouldProcess)]`)
- Prefer relative paths from a known root over absolute paths — makes scripts portable
- Log every file operation with `Write-Verbose` so `-Verbose` provides an audit trail
- For bulk operations, collect results into an array and report a summary at the end

## Avoid

- `Remove-Item -Recurse -Force` without a `ShouldProcess` guard
- Hardcoding absolute paths like `C:\Users\john\...`
- Silently overwriting files with `-Force` without logging
- Using `[System.IO.File]::Delete()` — prefer cmdlets that respect `-WhatIf`
- Expanding archives without checking free disk space for large files
