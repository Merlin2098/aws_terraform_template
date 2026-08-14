# Environment Detection

## When to use

- Before generating any shell script — Bash or PowerShell
- When the target platform is ambiguous (Windows native, WSL, Git Bash, Linux)
- When a script must behave differently on PowerShell 5.1 vs 7+
- When the user hasn't specified the runtime environment

## Default assumption

On Windows, assume **Git Bash** as the primary shell unless there is a
concrete signal otherwise (see `ai/domains/shell.md` §Shell precedence for
the full rule). Generate a Bash script by default. Fall back to PowerShell
only when the task needs a Windows-only capability Git Bash cannot provide
(services, registry, scheduled tasks, native `-WhatIf`) or when explicit
signals below point to a PowerShell-only session.

## Detection approach

Always determine the environment before writing a single line of script. Ask or detect:

| Signal | How to detect |
|---|---|
| OS family | `uname -s` (Bash/Git Bash) · `$PSVersionTable.OS` (PS) |
| Git Bash | `$MSYSTEM` is set (e.g. `MINGW64`) — treat as the default Windows shell when present |
| Shell type | `$BASH_VERSION` → Bash/Git Bash · `$PSVersionTable` present → PowerShell |
| PowerShell version | `$PSVersionTable.PSVersion.Major` — 5 = Windows PS, 7+ = PS Core |
| WSL | `uname -r` contains `microsoft` or `WSL` |
| macOS | `uname -s` = `Darwin` |

## Expected output (document in script header)

```yaml
environment:
  os: windows          # windows | linux | macos
  shell: gitbash        # gitbash | bash | powershell
  shell_version: 7.5   # PowerShell only
  wsl_enabled: false   # true | false | unknown
  git_bash: true
```

## Bash / Git Bash detection snippet

```bash
#!/usr/bin/env bash
IS_GIT_BASH=false
[[ -n "${MSYSTEM:-}" ]] && IS_GIT_BASH=true

IS_WSL=false
if grep -qi microsoft /proc/version 2>/dev/null; then IS_WSL=true; fi
```

## PowerShell detection snippet (fallback path only)

```powershell
$isPS7Plus = $PSVersionTable.PSVersion.Major -ge 7
$isWSL     = (Get-Item WSL:\ -ErrorAction SilentlyContinue) -ne $null
```

## Best practices

- Default to Git Bash on Windows; never assume PowerShell just because the OS is Windows
- Generate a single Bash script by default — only add a PowerShell variant
  when the task genuinely needs a Windows-only capability, and say so
  explicitly rather than generating both "just in case"
- Prefer `#!/usr/bin/env bash` (portable) over `/bin/bash` (absolute path)
- Prefer `pwsh` (PS 7+) over `powershell.exe` (PS 5.1) when PowerShell is the right tool; call out when PS 5.1-only cmdlets are needed

## Avoid

- Writing platform-specific scripts without documenting the target environment in the header
- Hardcoding `C:\` paths in scripts intended to run in Git Bash, WSL, or Linux — prefer `/c/...`-style or portable paths
- Generating a PowerShell script by default on Windows when Git Bash covers the task
- Combining OS-detection logic with business logic in the same function
