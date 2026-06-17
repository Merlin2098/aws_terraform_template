# PowerShell Core Patterns

## When to use

- Generating any PowerShell script (`.ps1`, module, function)
- Reviewing or refactoring existing PowerShell code
- Choosing between PowerShell approaches (cmdlet vs .NET vs COM)

## Idiomatic structure

### Function template

```powershell
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)][string]$Name,
    [string]$Environment = $env:APP_ENV ?? 'dev'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-SomeOperation {
    [CmdletBinding(SupportsShouldProcess)]
    param([string]$Target)

    Write-Verbose "Operating on: $Target"
    if ($PSCmdlet.ShouldProcess($Target, 'SomeOperation')) {
        # do work
    }
}
```

### Error handling

Use `try/catch/finally` with typed exceptions; never rely on `$?` alone:

```powershell
try {
    $result = Invoke-RestMethod -Uri $Uri -Method Get
}
catch [System.Net.WebException] {
    Write-Error "Network failure: $_"
    throw
}
finally {
    # cleanup regardless
}
```

### Structured logging (prefer over Write-Host)

```powershell
Write-Verbose  "Diagnostic detail (shown with -Verbose)"
Write-Debug    "Trace-level detail (shown with -Debug)"
Write-Warning  "Non-fatal condition"
Write-Error    "Failure — sets $? = $false"
# throw for hard stops, not exit 1
```

### Pipeline patterns

```powershell
Get-ChildItem -Path $Path -Recurse |
    Where-Object { $_.Extension -eq '.log' } |
    Select-Object Name, LastWriteTime |
    Sort-Object LastWriteTime -Descending
```

## Best practices

- Always set `$ErrorActionPreference = 'Stop'` at script top — prevents silent failures
- Always set `Set-StrictMode -Version Latest` — catches undefined variables
- Use `[CmdletBinding()]` on every function to get `-Verbose`, `-Debug`, `-WhatIf` for free
- Prefer named parameters over positional; use `[Parameter(Mandatory)]` explicitly
- Use `??` null-coalescing (PS 7+) or `if ($null -eq $x)` (PS 5.1) — never `if (!$x)` for null checks
- Return structured objects (`[PSCustomObject]`), not strings, from functions

## Avoid

```powershell
Write-Host "error message"   # bypasses pipeline, not suppressible
exit 1                        # use throw instead — gives callers a catchable exception
$Error[0]                     # fragile; use try/catch
if ($?) { ... }               # unreliable for complex command chains
```

- Mixing UI output (`Write-Host`) with pipeline output (`Write-Output`)
- Using `Invoke-Expression` — prefer direct cmdlet calls
- Using `-ErrorAction SilentlyContinue` without a reason comment

## PS 5.1 vs 7+ compatibility

| Feature | PS 5.1 | PS 7+ |
|---|---|---|
| Null coalescing `??` | No | Yes |
| `foreach -Parallel` | No | Yes |
| `ConvertFrom-Json -AsHashtable` | No | Yes |
| Cross-platform | Windows only | Windows/Linux/macOS |

When the script must run on PS 5.1, avoid 7+ syntax. When targeting PS 7+, document it in the header comment. See `ai/skills/shell/environment_detection.md` for detection patterns.
