# Install GNU Make on Windows

Use this guide when you need a clear Windows setup path for:

- GNU Make with administrator rights and automatic `PATH` integration
- GNU Make without administrator rights using manual binaries and manual setup

This guide is intentionally split into `PATH` and corporate/manual flows so the
operational difference stays explicit. Once `make.exe` is on `PATH`, Git Bash
runs `make <target>` directly — no wrapper needed (see
[make_cheatlist.md](make_cheatlist.md)). The Chocolatey installer itself
requires an elevated PowerShell session (Windows has no admin-elevated Git
Bash equivalent); verification afterward works from either shell.

## 1. GNU Make With Administrator Rights

Use this path when you control the machine and want `make.exe` installed in a
standard way that becomes available in `PATH`.

### Install Chocolatey

Open PowerShell as Administrator (required — this step needs Windows
elevation, which Git Bash cannot request on its own).

If needed, relax the execution policy for the current session:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
```

Install Chocolatey:

```powershell
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

Close and reopen your shell (Git Bash or PowerShell), then verify:

```bash
choco --version
```

Reference: https://docs.chocolatey.org/en-us/choco/setup/

### Install Make With Chocolatey

Still from an elevated PowerShell session:

```powershell
choco install make -y
```

Close and reopen Git Bash (or PowerShell), then verify:

```bash
make --version
which make
```

Expected behavior:

- `make` is available directly in `PATH` in both Git Bash and PowerShell
- Git Bash calls `make <target>` directly; `scripts/windows/run_make.ps1`
  (PowerShell fallback) also resolves `make` from `PATH` first

Reference: https://community.chocolatey.org/packages/make

### Add Make to PATH Permanently (PowerShell, Admin)

If `make.exe` is already installed but not yet in the system `PATH`, run this
once from an Administrator PowerShell session:

```powershell
$makePath = (Get-Command make -ErrorAction SilentlyContinue)?.Source |
    Split-Path -Parent

if (-not $makePath) {
    # Chocolatey default location — adjust if installed elsewhere
    $makePath = "$env:ChocolateyInstall\bin"
}

[System.Environment]::SetEnvironmentVariable(
    "Path",
    [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";$makePath",
    "Machine"
)
Write-Host "Added to system PATH: $makePath"
```

Close and reopen your shell (Git Bash or PowerShell), then verify:

```bash
make --version
which make
```

This writes to the **Machine** scope so the change persists for all users and
survives reboots. Use scope `"User"` instead if you only want it for your
profile and do not have admin rights.

## 2. GNU Make Without Administrator Rights

Use this path when you cannot install system-wide tools and must keep the setup
inside a user-controlled folder.

### Option A: Use an Approved Corporate Binary Folder

If your company provides an approved `make.exe`, place it in a known location,
for example:

```text
C:\approved-tools\make\bin\make.exe
```

Verify it directly:

```bash
/c/approved-tools/make/bin/make.exe --version
```

### Option B: Add the Binary Folder to the Current Session PATH

If session-level `PATH` changes are allowed, in Git Bash:

```bash
export PATH="/c/approved-tools/make/bin:$PATH"
make --version
which make
```

PowerShell equivalent:

```powershell
$env:Path = "C:\approved-tools\make\bin;$env:Path"
make --version
```

This gives you a `PATH`-style workflow without requiring admin rights.

### Option C: Keep the Binary Out of PATH

If you want an explicit corporate path and do not want to touch `PATH`, in Git
Bash:

```bash
/c/approved-tools/make/bin/make.exe test
/c/approved-tools/make/bin/make.exe package
```

Or, from PowerShell without a POSIX shell available, use the repository
wrapper:

```powershell
.\scripts\windows\run_make.ps1 -MakePath 'C:\approved-tools\make\bin\make.exe' test
```

### How the Template Wrapper Behaves

`scripts/windows/run_make.ps1` currently resolves make in this order:

1. `-MakePath` if you pass it explicitly
2. `make` already available in `PATH`
3. `where.exe make.exe`
4. filesystem discovery for `make.exe`

That means:

- admin installs through Chocolatey usually hit the `PATH` case
- corporate/manual installs can use `-MakePath` or be discovered from known folders

## 3. Recommended Operational Choices

For GNU Make:

- Prefer the Chocolatey install when admin rights are available and a normal
  `PATH` workflow is acceptable — this is what lets Git Bash run `make`
  directly, matching Linux/WSL.
- Prefer the explicit binary + wrapper path when the machine is restricted.

## 4. Quick Verification Commands

Git Bash:

```bash
make --version
make -n test
```

PowerShell fallback (no `make.exe` on `PATH`):

```powershell
.\scripts\windows\run_make.ps1
.\scripts\windows\run_make.ps1 -n test
```

For ready-to-copy `make` command examples, see [make_cheatlist.md](make_cheatlist.md).

For uv installation and validation, see [uv_install.md](uv_install.md).
