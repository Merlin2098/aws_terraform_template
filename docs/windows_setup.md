# Windows Setup

This guide prepares a Windows machine to use this template and to install it into
another repository.

## 1. Install Chocolatey

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

## 2. Install GNU Make

Open PowerShell as Administrator:

```powershell
choco install make -y
```

Close and reopen PowerShell, then verify:

```powershell
make --version
```

Reference: https://community.chocolatey.org/packages/make

## 3. Prepare Python and Pre-commit

From the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.local.txt -r requirements.dev.txt
.\.venv\Scripts\pre-commit.exe install
```

`requirements.local.txt` installs the local developer environment. Deployment bundles use
`requirements.cloud.txt` during packaging.

When you install this template into another repository, the local profile copies
`requirements.local.txt` plus `requirements.dev.txt`. The cloud profile copies
`requirements.local.txt`, `requirements.cloud.txt`, and `requirements.dev.txt`
so a local MVP can evolve into a cloud-ready project.

Verify pre-commit:

```powershell
.\.venv\Scripts\pre-commit.exe --version
```

To run all configured hooks manually:

```powershell
.\.venv\Scripts\pre-commit.exe run --all-files
```

Reference: https://pre-commit.com/

## 4. Install This Template Into Another Repo

Preview the install without writing files:

```powershell
.\.venv\Scripts\python.exe main.py --dry-run --target C:\path\to\target-repo
```

Install the template by selecting the target repository folder in Explorer:

```powershell
.\.venv\Scripts\python.exe main.py
```

Install the template with an explicit target path:

```powershell
.\.venv\Scripts\python.exe main.py --target C:\path\to\target-repo
```

Overwrite existing target files only when intentional:

```powershell
.\.venv\Scripts\python.exe main.py --target C:\path\to\target-repo --force
```

The installer copies template files into the target repository and adds these
entries to the target `.gitignore` if they are missing:

```gitignore
ai/
AGENTS.md
Makefile
```

The installer does not run Terraform, install dependencies, initialize Git, or
execute pre-commit in the target repository.

The installer also leaves the installer and template docs behind: `main.py`,
files named `README.md`, and `docs/` are not copied to the target repository.
