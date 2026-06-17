# Environment Detection

## When to use

- Before generating any shell script — Bash or PowerShell
- When the target platform is ambiguous (Windows native, WSL, Git Bash, Linux)
- When a script must behave differently on PowerShell 5.1 vs 7+
- When the user hasn't specified the runtime environment

## Detection approach

Always determine the environment before writing a single line of script. Ask or detect:

| Signal | How to detect |
|---|---|
| OS family | `$PSVersionTable.OS` (PS) · `uname -s` (Bash) |
| Shell type | `$PSVersionTable` present → PowerShell · `$BASH_VERSION` → Bash |
| PowerShell version | `$PSVersionTable.PSVersion.Major` — 5 = Windows PS, 7+ = PS Core |
| WSL | `uname -r` contains `microsoft` or `WSL` |
| Git Bash | `$MSYSTEM` is set (e.g. `MINGW64`) |
| macOS | `uname -s` = `Darwin` |

## Expected output (document in script header)

```yaml
environment:
  os: windows          # windows | linux | macos
  shell: powershell    # powershell | bash
  shell_version: 7.5
  wsl_enabled: true    # true | false | unknown
  git_bash: false
```

## PowerShell detection snippet

```powershell
$isPS7Plus = $PSVersionTable.PSVersion.Major -ge 7
$isWSL     = (Get-Item WSL:\ -ErrorAction SilentlyContinue) -ne $null
```

## Bash detection snippet

```bash
#!/usr/bin/env bash
IS_WSL=false
if grep -qi microsoft /proc/version 2>/dev/null; then IS_WSL=true; fi
```

## Best practices

- Default to the environment detected at script entry; never assume
- When both Bash and PowerShell are plausible, generate both variants and note which is primary
- Prefer `#!/usr/bin/env bash` (portable) over `/bin/bash` (absolute path)
- Prefer `pwsh` (PS 7+) over `powershell.exe` (PS 5.1) for cross-platform scripts; call out when PS 5.1-only cmdlets are needed

## Avoid

- Writing platform-specific scripts without documenting the target environment in the header
- Hardcoding `C:\` paths in scripts intended for Linux/WSL
- Assuming `bash` is available on Windows native (Git Bash or WSL must be confirmed)
- Combining OS-detection logic with business logic in the same function
