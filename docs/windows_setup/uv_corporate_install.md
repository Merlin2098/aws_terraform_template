# Install uv In Restricted Corporate Windows Environments

Use this flow when:

- Python is already installed on the machine
- corporate policy blocks the standalone `uv` installer
- `python` is not reliably available in `PATH`
- you need one explicit way to install and run `uv`

This approach installs `uv` with `pip` through the approved Python executable,
then keeps a single explicit command pattern for future `uv` usage.

## 1. Find the Python Executable

First verify where Python is installed.

If `python` is already available in `PATH`:

```powershell
Get-Command python
python -V
```

If your environment uses the Windows launcher:

```powershell
py -0p
```

If neither command is available, check the approved machine install path
provided by your workstation image or support team, for example:

```powershell
Test-Path "C:\Program Files\Python314\python.exe"
```

Once confirmed, keep the full path to `python.exe`.

Example:

```text
C:\Program Files\Python314\python.exe
```

## 2. Install uv With pip Through That Python

Run `pip install uv` by calling the exact Python executable path.

Example:

```powershell
& 'C:\Program Files\Python314\python.exe' -m pip install uv
```

Then verify that `uv` is available through the same Python:

```powershell
& 'C:\Program Files\Python314\python.exe' -m uv --version
```

This avoids depending on `PATH` changes or a separately installed `uv.exe`.

## 3. Define the Universal uv Command

After installation, keep one explicit command pattern for `uv`:

```powershell
$UV="& 'C:\Program Files\Python314\python.exe' -m uv"
```

You can then run `uv` subcommands consistently with:

```powershell
Invoke-Expression "$UV --version"
Invoke-Expression "$UV venv .venv"
Invoke-Expression "$UV sync"
Invoke-Expression "$UV tree"
Invoke-Expression "$UV pip list --python .venv\Scripts\python.exe"
```

This is useful on locked-down machines because it:

- avoids relying on `uv` being in `PATH`
- avoids relying on `python` being in `PATH`
- keeps the execution path explicit for support and troubleshooting

## Recommended Operational Pattern

For restricted corporate Windows hosts, prefer this order:

1. Verify the approved Python executable path.
2. Install `uv` using that Python with `-m pip install uv`.
3. Run `uv` using the same Python with `-m uv`.
4. Reuse the same universal command string in setup and diagnostics.

## Example Session

```powershell
Test-Path "C:\Program Files\Python314\python.exe"
& 'C:\Program Files\Python314\python.exe' -m pip install uv
& 'C:\Program Files\Python314\python.exe' -m uv --version
$UV="& 'C:\Program Files\Python314\python.exe' -m uv"
Invoke-Expression "$UV sync"
Invoke-Expression "$UV tree"
```

## Notes

- Replace `C:\Program Files\Python314\python.exe` with the real approved Python
  path on the machine.
- If corporate policy also blocks `pip install`, coordinate with the platform or
  security team for an approved internal installation path.
- If the host later shows package-refresh warnings for a uv-managed `.venv`,
  see [README.md](README.md) for the Windows troubleshooting note.
