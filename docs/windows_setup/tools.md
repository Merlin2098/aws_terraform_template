# Windows Tooling Setup

Install the local Windows tools needed by this template. Use the admin path when
you control the machine, or the no-admin path when corporate policy blocks UAC or
system-wide installs.

## Install Chocolatey

Open PowerShell as Administrator and verify the execution policy:

```powershell
Get-ExecutionPolicy
```

If it returns `Restricted`, use a process-scoped policy for the install session:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
```

Install Chocolatey:

```powershell
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

Close and reopen PowerShell, then verify:

```powershell
choco --version
```

Reference: https://docs.chocolatey.org/en-us/choco/setup/

## Install GNU Make With Admin Rights

Open PowerShell as Administrator:

```powershell
choco install make -y
```

Close and reopen PowerShell, then verify:

```powershell
make --version
```

Reference: https://community.chocolatey.org/packages/make

## Install GNU Make Without Admin Rights

Scoop installs command-line tools into the current user's home directory, so it
does not require administrator permissions by default.

Open a regular, non-admin PowerShell window:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

Install Make:

```powershell
scoop install make
make --version
```

If your company blocks Scoop but provides an approved `make.exe`, call it directly
or add it to the current PowerShell session:

```powershell
C:\approved-tools\make\bin\make.exe --version
$env:Path = "C:\approved-tools\make\bin;$env:Path"
make --version
```

Use the explicit executable path in locked-down shells if `PATH` changes are also
blocked:

```powershell
C:\approved-tools\make\bin\make.exe package
C:\approved-tools\make\bin\make.exe test
```

References:

- https://scoop.sh/
- https://github.com/ScoopInstaller/Scoop

## Install uv From PowerShell

Use uv when you want faster virtual environment and `requirements.txt` workflows.
The official standalone installer does not require Python to already be available.

If Python is available in `PATH`, install uv with pip:

```powershell
python -m pip install uv
python -m uv --version
```

If Python is installed but corporate policy does not expose `python` in `PATH`, use
the standalone PowerShell installer instead:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen PowerShell, then verify:

```powershell
uv --version
```

If the standalone installer is also blocked by policy, ask your platform or
security team to provide an approved `uv.exe` location, then call it explicitly:

```powershell
C:\approved-tools\uv\uv.exe --version
```

Reference: https://docs.astral.sh/uv/getting-started/installation/

## Use uv With requirements.txt

For a requirements-based project, keep `requirements.txt` as the dependency input
and let uv install or synchronize the virtual environment.

When `uv` is available in `PATH`:

```powershell
uv venv .venv
uv pip install -r requirements.txt
```

Use `sync` when the virtual environment should match `requirements.txt` exactly:

```powershell
uv pip sync requirements.txt
```

When Python is available in `PATH` but the `uv` command is not:

```powershell
python -m uv venv .venv
python -m uv pip install -r requirements.txt
python -m uv pip sync requirements.txt
```

When neither `python` nor `uv` is available in `PATH`, call the approved uv binary
directly:

```powershell
C:\approved-tools\uv\uv.exe venv .venv
C:\approved-tools\uv\uv.exe pip install -r requirements.txt
C:\approved-tools\uv\uv.exe pip sync requirements.txt
```

To maintain pinned requirements from an input file, keep loose dependencies in
`requirements.in` and regenerate `requirements.txt` explicitly:

```powershell
uv pip compile requirements.in -o requirements.txt
uv pip compile requirements.in -o requirements.txt --upgrade
```

References:

- https://docs.astral.sh/uv/pip/packages/
- https://docs.astral.sh/uv/pip/compile/
