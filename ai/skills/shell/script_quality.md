# Script Quality: Testing, Documentation, and Refactoring

## When to use

- After generating a Bash or PowerShell script — add documentation and validate it
- Before committing or sharing a script
- When reviewing or improving an existing script

---

## Testing

### Bash — ShellCheck

Every generated Bash script should pass ShellCheck without critical errors:

```bash
# Install
# Ubuntu/WSL: sudo apt-get install shellcheck
# macOS:      brew install shellcheck
# Windows:    scoop install shellcheck  or  via Git Bash

shellcheck script.sh
shellcheck --severity=warning script.sh  # raise the bar
```

Common ShellCheck findings to fix before shipping:

| Code | Problem | Fix |
|---|---|---|
| SC2086 | Unquoted variable | Quote: `"$VAR"` |
| SC2046 | Unquoted command substitution | Use `"$(cmd)"` |
| SC2164 | `cd` without error check | Use `cd ... \|\| die "..."` |
| SC2006 | Backtick command substitution | Use `$(...)` |
| SC1091 | Can't follow sourced file | Add `# shellcheck source=...` hint |

### PowerShell — PSScriptAnalyzer

```powershell
# Install once
Install-Module -Name PSScriptAnalyzer -Scope CurrentUser -Force

# Analyze a script
Invoke-ScriptAnalyzer -Path .\script.ps1

# Analyze with all rules (stricter)
Invoke-ScriptAnalyzer -Path .\script.ps1 -IncludeDefaultRules
```

Common PSScriptAnalyzer rules:

| Rule | Problem | Fix |
|---|---|---|
| PSAvoidUsingWriteHost | Use `Write-Host` | Replace with `Write-Verbose`/`Write-Output` |
| PSAvoidUsingPlainTextForPassword | Plain text password param | Use `[SecureString]` |
| PSUseShouldProcessForStateChangingFunctions | Missing `ShouldProcess` | Add `[CmdletBinding(SupportsShouldProcess)]` |
| PSAvoidGlobalVars | Global variable usage | Refactor to parameters/returns |

### PowerShell — Pester (unit tests)

For reusable functions, generate a Pester test file alongside the script:

```powershell
# tests/Get-BucketName.Tests.ps1
Describe 'Get-BucketName' {
    It 'returns correct name for dev' {
        Get-BucketName -Project 'app' -Env 'dev' | Should -Be 'app-dev-data'
    }

    It 'throws on empty project' {
        { Get-BucketName -Project '' -Env 'dev' } | Should -Throw
    }
}
```

Run: `Invoke-Pester -Path tests/ -Output Detailed`

---

## Documentation

### PowerShell — comment-based help

Every exported function or script must include:

```powershell
<#
.SYNOPSIS
    One-line description of what the script does.

.DESCRIPTION
    Longer description. Include environment requirements, side effects,
    and any approval requirements (e.g., "terraform apply requires user approval").

.PARAMETER Name
    Description of the Name parameter.

.PARAMETER Environment
    Target environment (dev, staging, prod). Defaults to $env:APP_ENV or 'dev'.

.EXAMPLE
    .\Deploy-Lambda.ps1 -Name my-function -Environment dev
    Deploys the Lambda function to the dev environment.

.EXAMPLE
    .\Deploy-Lambda.ps1 -Name my-function -WhatIf
    Shows what would happen without making changes.

.NOTES
    Requires: AWS CLI configured, terraform >= 1.5
    Approval: terraform apply requires explicit confirmation.
#>
```

Access with: `Get-Help .\script.ps1 -Full`

### Bash — script header

Every Bash script must include a header block:

```bash
#!/usr/bin/env bash
set -euo pipefail
# ---------------------------------------------------------------------------
# Script:  deploy.sh
# Purpose: Deploy Lambda function from local artifact to S3 and update code.
# Usage:   ./deploy.sh --env dev [--dry-run]
# Requires: aws CLI, jq, terraform (for output reads)
# Approval: terraform apply requires explicit user confirmation.
# ---------------------------------------------------------------------------
```

---

## Refactoring

Apply these improvements when reviewing or improving existing scripts:

### Extract repeated logic into functions

```bash
# BEFORE: repeated pattern
aws s3 cp file1.zip "s3://$BUCKET/"
if [[ $? -ne 0 ]]; then echo "upload failed"; exit 1; fi
aws s3 cp file2.zip "s3://$BUCKET/"
if [[ $? -ne 0 ]]; then echo "upload failed"; exit 1; fi

# AFTER: function
upload_to_s3() {
    local file="$1"
    aws s3 cp "$file" "s3://$BUCKET/" || die "upload failed: $file"
}
upload_to_s3 file1.zip
upload_to_s3 file2.zip
```

### Simplify conditional logic

```powershell
# BEFORE: nested ifs
if ($a) {
    if ($b) {
        if ($c) { DoThing }
    }
}

# AFTER: guard clauses
if (-not $a) { return }
if (-not $b) { return }
if (-not $c) { return }
DoThing
```

### Replace magic strings with named constants

```bash
# BEFORE
sleep 30

# AFTER
readonly UPLOAD_WAIT_SECONDS=30
sleep $UPLOAD_WAIT_SECONDS
```

### Refactoring checklist

- [ ] Duplicate code → extract function
- [ ] Magic numbers/strings → named constants
- [ ] Deep nesting → guard clauses / early returns
- [ ] Long scripts (>150 lines) → split into sourced modules
- [ ] Undocumented parameters → add `--help` or comment-based help
- [ ] Silent failures → explicit error handling with `die`/`throw`

## Avoid

- Shipping scripts without ShellCheck or PSScriptAnalyzer passing
- Scripts longer than ~150 lines without function decomposition
- Copying and pasting error-handling blocks instead of abstracting to a function
- Skipping documentation on scripts that will be run by others
