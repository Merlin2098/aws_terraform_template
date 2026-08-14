# Domain: Shell / Scripting

## Purpose

Guidance for generating, validating, and maintaining shell scripts in Bash and
PowerShell for Windows, Linux, WSL, and Git Bash environments. This domain
covers environment detection, idiomatic scripting patterns, Windows
administration, CLI orchestration, security, testing, and documentation.

It is the authoritative source for *how to write and validate scripts* — not
for what AWS services do (see `ai/domains/aws.md`) or how Terraform modules are
structured (see `ai/domains/terraform.md`).

---

## Shell precedence

**Git Bash is the primary shell on Windows.** PowerShell is a documented
fallback, not a symmetric alternative generated "just in case." Apply this
order:

1. **Git Bash** (`$MSYSTEM` set, e.g. `MINGW64`) — default assumption on
   Windows when no other signal overrides it. Generate Bash scripts;
   `ai/skills/shell/bash_core.md` already treats Git Bash as a first-class
   target (see its Portable Compatibility table).
2. **Linux / WSL / macOS** — Bash, same skill tree as Git Bash.
3. **PowerShell** — only when the task needs a capability Git Bash cannot
   provide: Windows services, registry, scheduled tasks, native
   `-WhatIf`/`ShouldProcess` semantics, or the user's session is confirmed
   PowerShell-only (no `$MSYSTEM`, `$PSVersionTable` present).

Do not generate both a Bash and a PowerShell variant by default. Generate one,
matching the precedence above, and only add the other when the task explicitly
requires the fallback capability — say so when it happens.

`docs/windows_setup/` follows this precedence: Git Bash commands
(`scripts/linux/*.sh`, direct `make`) are shown first, with the PowerShell
equivalent (`scripts/windows/*.ps1`) as a labelled fallback.

---

## Scope

| In scope | Out of scope |
|---|---|
| Bash and PowerShell script structure and idioms | AWS service behaviour and configuration (→ `ai/domains/aws.md`) |
| Environment detection (OS, shell, WSL, Git Bash) | Terraform module design (→ `ai/domains/terraform.md`) |
| Safe filesystem, services, registry, and scheduled-task operations | Python automation (→ `ai/domains/python.md`) |
| CLI orchestration (git, terraform, docker, aws, az) — scripting patterns | CI/CD pipeline configuration syntax (→ `ai/skills/terraform/terraform_ci_cd.md`) |
| Script security: destructive-op guards, dry-run, secret hygiene | Internal framework or runtime implementation |
| Script testing (ShellCheck, PSScriptAnalyzer, Pester) and documentation | Operational AWS smoke testing templates (→ `ai/skills/aws/aws_smoke_testing.md`) |

---

## Skills

| Skill | File | Description |
|---|---|---|
| Environment detection | `ai/skills/shell/environment_detection.md` | Detect OS, shell type, PowerShell version, WSL, and Git Bash before generating scripts |
| PowerShell core | `ai/skills/shell/powershell_core.md` | Idiomatic PowerShell — cmdlets, error handling, structured logging, pipeline patterns |
| PowerShell filesystem | `ai/skills/shell/powershell_filesystem.md` | Safe file/directory operations with mandatory `-WhatIf` on destructive commands |
| PowerShell Windows admin | `ai/skills/shell/powershell_windows_admin.md` | Services, registry (with backup), and scheduled tasks |
| PowerShell JSON/YAML | `ai/skills/shell/powershell_json_yaml.md` | JSON and YAML parsing and serialization in PowerShell |
| Bash core | `ai/skills/shell/bash_core.md` | Portable Bash scripts — `set -euo pipefail`, error handling, arg parsing |
| CLI automation | `ai/skills/shell/cli_automation.md` | Safe scripting for git, terraform, docker, aws, az |
| Script security | `ai/skills/shell/script_security.md` | Destructive-op guards, dry-run, confirmation prompts, secret hygiene |
| Script quality | `ai/skills/shell/script_quality.md` | ShellCheck, PSScriptAnalyzer, Pester, documentation, and refactoring patterns |

---

## Skill dependency order

```
environment_detection
    └── bash_core                  (default — Git Bash / Linux / WSL / macOS)
            └── cli_automation
    └── powershell_core            (fallback — Windows-only capability needed)
            ├── powershell_filesystem
            ├── powershell_windows_admin
            └── powershell_json_yaml

script_security      (applies to all scripts regardless of shell)
script_quality       (applies to all scripts regardless of shell)
```

Always apply `environment_detection` first. Per the precedence rule above,
default to the `bash_core` tree; only descend into the `powershell_core` tree
when the task needs a Windows-only capability. Layer `script_security` and
`script_quality` on every generated script.

---

## Policies

This domain is subject to the global policies in [`ai/policies/global.md`](../policies/global.md).

Key constraints:

- **Policy 008 (Simplicity)** — apply the simplicity ladder before introducing
  abstractions; three similar lines is better than a premature helper function.
- **AGENTS.md — Approval Boundaries** — `terraform apply`, `terraform destroy`,
  and overwriting user-owned data always require explicit approval. Scripts that
  invoke these must implement a confirmation gate (see `ai/skills/shell/script_security.md`).
- **AC-3 / AC-4 (SPEC-018)** — all destructive operations require confirmation;
  PowerShell scripts support `-WhatIf` where applicable.

Scripts in this domain may *invoke* AWS and Terraform CLI. The resulting
infrastructure changes remain subject to the approval rules in AGENTS.md and
SPEC-009 (`ai/policies/global.md` §Policy 009).
