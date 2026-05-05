param(
    [string]$PythonPath,
    [ValidateSet("local", "cloud")]
    [string]$Profile = "local",
    [switch]$IncludeDev,
    [switch]$NoDev
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($IncludeDev -and $NoDev) {
    throw "Use either -IncludeDev or -NoDev, but not both."
}

$useDevDependencies = $true
if ($NoDev) {
    $useDevDependencies = $false
}

function Write-Step {
    param(
        [string]$Message,
        [ConsoleColor]$Color = [ConsoleColor]::Yellow
    )

    Write-Host $Message -ForegroundColor $Color
}

function Write-Phase {
    param(
        [string]$Title
    )

    Write-Host ""
    Write-Host "=== $Title ===" -ForegroundColor Cyan
}

function Assert-PythonPath {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Python not found at '$Path'."
    }
}

function New-PythonCommand {
    param(
        [string]$Command,
        [string[]]$BaseArguments,
        [string]$Description
    )

    return [pscustomobject]@{
        Command = $Command
        BaseArguments = $BaseArguments
        Description = $Description
    }
}

function Test-PythonCommand {
    param(
        [pscustomobject]$PythonCommand
    )

    & $PythonCommand.Command @($PythonCommand.BaseArguments + @("--version")) *> $null
    return $LASTEXITCODE -eq 0
}

function Resolve-PythonCommand {
    param(
        [string]$ExplicitPythonPath
    )

    $attemptedResolvers = @()
    $venvPython = ".venv\Scripts\python.exe"

    if (Test-Path -LiteralPath $venvPython) {
        $venvCommand = New-PythonCommand -Command $venvPython -BaseArguments @() -Description "existing .venv interpreter"
        $attemptedResolvers += $venvCommand.Description
        if (Test-PythonCommand -PythonCommand $venvCommand) {
            return $venvCommand
        }
    }

    if ($ExplicitPythonPath) {
        $attemptedResolvers += "explicit path '$ExplicitPythonPath'"
        Assert-PythonPath -Path $ExplicitPythonPath
        $pythonCommand = New-PythonCommand -Command $ExplicitPythonPath -BaseArguments @() -Description "explicit path '$ExplicitPythonPath'"
        if (-not (Test-PythonCommand -PythonCommand $pythonCommand)) {
            throw "Python at '$ExplicitPythonPath' did not respond correctly."
        }
        return $pythonCommand
    }

    $candidates = @(
        (New-PythonCommand -Command "py" -BaseArguments @("-3") -Description "py -3"),
        (New-PythonCommand -Command "python" -BaseArguments @() -Description "python from PATH")
    )

    foreach ($candidate in $candidates) {
        $attemptedResolvers += $candidate.Description
        if (Test-PythonCommand -PythonCommand $candidate) {
            return $candidate
        }
    }

    $attemptedText = $attemptedResolvers -join ", "
    throw "Unable to resolve a working Python interpreter. Tried: $attemptedText. Install/configure Python or pass -PythonPath."
}

function Invoke-PythonCommand {
    param(
        [pscustomobject]$PythonCommand,
        [string[]]$Arguments
    )

    $allArguments = @($PythonCommand.BaseArguments + $Arguments)
    & $PythonCommand.Command @allArguments
    if ($LASTEXITCODE -ne 0) {
        $joinedArguments = $allArguments -join " "
        throw "Command failed: $($PythonCommand.Command) $joinedArguments"
    }
}

function Assert-UvAvailable {
    param(
        [pscustomobject]$PythonCommand
    )

    try {
        Invoke-PythonCommand -PythonCommand $PythonCommand -Arguments @("-m", "uv", "--version")
    }
    catch {
        throw "uv is not available through '$($PythonCommand.Description)'. Install uv for that interpreter and try again."
    }
}

function Assert-ProjectState {
    if (-not (Test-Path -LiteralPath "pyproject.toml")) {
        throw "pyproject.toml is required for the uv update flow."
    }

    if (-not (Test-Path -LiteralPath ".venv")) {
        throw "No .venv directory was found. Run .\scripts\windows\setup_env.ps1 first."
    }
}

function Get-UvSyncArguments {
    param(
        [string]$SelectedProfile,
        [bool]$UseDevDependencies
    )

    $arguments = @("-m", "uv", "sync", "--extra", "local")

    if ($SelectedProfile -eq "cloud") {
        $arguments += @("--extra", "cloud")
    }

    if ($UseDevDependencies) {
        $arguments += @("--group", "dev")
    } else {
        $arguments += "--no-dev"
    }

    return $arguments
}

Write-Step "Starting virtual environment update from uv project files." ([ConsoleColor]::Cyan)

Write-Phase "Phase 1: Resolve Python"
$pythonCommand = Resolve-PythonCommand -ExplicitPythonPath $PythonPath
Write-Step "[Python] Using interpreter resolved via $($pythonCommand.Description)." ([ConsoleColor]::DarkCyan)

Write-Step "[Python] Validating the selected Python interpreter..." ([ConsoleColor]::Yellow)
Invoke-PythonCommand -PythonCommand $pythonCommand -Arguments @("--version")

Write-Phase "Phase 2: Validate Tooling"
Write-Step "[uv] Checking whether uv is available for the selected interpreter..." ([ConsoleColor]::Yellow)
Assert-UvAvailable -PythonCommand $pythonCommand

Write-Step "[Project] Verifying project state and existing virtual environment..." ([ConsoleColor]::Yellow)
Assert-ProjectState

$syncArguments = Get-UvSyncArguments -SelectedProfile $Profile -UseDevDependencies:$useDevDependencies
$dependencyMode = if ($useDevDependencies) { "including dev dependencies" } else { "without dev dependencies" }

Write-Phase "Phase 3: Sync Dependencies"
Write-Step "[Dependencies] Syncing .venv for profile '$Profile' ($dependencyMode)..." ([ConsoleColor]::Yellow)
Invoke-PythonCommand -PythonCommand $pythonCommand -Arguments $syncArguments

$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"

Write-Phase "Phase 4: Summary"
Write-Step "Virtual environment updated successfully." ([ConsoleColor]::Green)
Write-Host "Profile synced: $Profile"
Write-Host "Dev dependencies enabled: $useDevDependencies"
Write-Host "Virtual environment path: .venv"
Write-Host "Suggested interpreter path: $venvPython"
