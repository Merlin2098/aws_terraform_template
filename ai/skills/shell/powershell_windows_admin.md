# PowerShell Windows Administration

Covers: Windows Services · Registry · Scheduled Tasks

## When to use

- Managing Windows services (start, stop, restart, query)
- Reading or writing Windows Registry keys with safety guarantees
- Creating, updating, querying, or removing Scheduled Tasks

---

## Services

### Pattern

```powershell
[CmdletBinding(SupportsShouldProcess)]
param([Parameter(Mandatory)][string]$ServiceName)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $svc) {
    Write-Error "Service not found: $ServiceName"
    return
}

Write-Verbose "Current status: $($svc.Status)"

if ($PSCmdlet.ShouldProcess($ServiceName, 'Restart-Service')) {
    Restart-Service -Name $ServiceName
    Write-Verbose "Restarted: $ServiceName"
}
```

### Rules

- Always check service existence with `Get-Service ... -ErrorAction SilentlyContinue` before Start/Stop/Restart
- Use `SupportsShouldProcess` + `ShouldProcess` on every state-changing operation
- After Start/Restart, validate the final status: `(Get-Service $Name).Status -eq 'Running'`
- Never use `net start` / `net stop` — use the PS cmdlets for structured error handling

---

## Registry

### Pattern

```powershell
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$KeyPath  = 'HKCU:\Software\MyApp',
    [string]$Name     = 'Setting',
    [string]$Value    = 'default'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Backup before modifying
$backup = "$env:TEMP\registry-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss').reg"
$hive = $KeyPath -replace '\\.*'   # e.g. HKCU
reg export ($KeyPath -replace 'HKCU:\\', 'HKCU\') $backup /y
Write-Verbose "Registry backup saved: $backup"

if (-not (Test-Path $KeyPath)) {
    if ($PSCmdlet.ShouldProcess($KeyPath, 'New-Item')) {
        New-Item -Path $KeyPath -Force | Out-Null
    }
}

if ($PSCmdlet.ShouldProcess("$KeyPath\$Name", 'Set-ItemProperty')) {
    Set-ItemProperty -Path $KeyPath -Name $Name -Value $Value
    Write-Verbose "Set $Name = $Value at $KeyPath"
}
```

### Rules

- **Always export a backup** (`reg export`) before writing or deleting any key
- Validate key/value existence with `Test-Path` and `Get-ItemProperty -ErrorAction SilentlyContinue`
- Never modify `HKLM:\SYSTEM` or security-related hives without documenting the reason
- Use `ShouldProcess` on every write/delete to support `-WhatIf`
- Provide a restore path: document how to apply the backup (`reg import <file>`)

---

## Scheduled Tasks

### Query

```powershell
Get-ScheduledTask -TaskName 'MyTask' -ErrorAction SilentlyContinue
```

### Create / Update (idempotent)

```powershell
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$TaskName    = 'MyBackupTask',
    [string]$ScriptPath  = 'C:\Scripts\backup.ps1',
    [string]$TriggerTime = '02:00'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$action  = New-ScheduledTaskAction -Execute 'pwsh.exe' -Argument "-NonInteractive -File `"$ScriptPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At $TriggerTime
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 1)

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existing) {
    if ($PSCmdlet.ShouldProcess($TaskName, 'Update-ScheduledTask')) {
        Set-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings
        Write-Verbose "Updated task: $TaskName"
    }
} else {
    if ($PSCmdlet.ShouldProcess($TaskName, 'Register-ScheduledTask')) {
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings
        Write-Verbose "Registered task: $TaskName"
    }
}
```

### Delete

```powershell
if ($PSCmdlet.ShouldProcess($TaskName, 'Unregister-ScheduledTask')) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}
```

### Rules

- Check task existence before create/update/delete — prefer idempotent upsert pattern above
- Always set an `ExecutionTimeLimit` — never let tasks run unbounded
- Run tasks as a service account, not interactively; document the principal in the script header
- Use `ShouldProcess` on all mutations

## Avoid

- Starting/stopping services or writing registry without existence check
- Writing registry without a backup
- Creating scheduled tasks with `-RunLevel Highest` unless elevation is explicitly required and documented
- Leaving `ExecutionTimeLimit` as default (PT72H) — set it explicitly
