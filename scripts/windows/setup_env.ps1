param(
    [string]$PythonPath = "C:\Program Files\Python314\python.exe",
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

function Assert-PythonPath {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Python not found at '$Path'."
    }
}

function Invoke-PythonCommand {
    param(
        [string]$Python,
        [string[]]$Arguments
    )

    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        $joinedArguments = $Arguments -join " "
        throw "Command failed: $Python $joinedArguments"
    }
}

function Assert-UvAvailable {
    param(
        [string]$Python
    )

    try {
        Invoke-PythonCommand -Python $Python -Arguments @("-m", "uv", "--version")
    }
    catch {
        throw "uv is not available through '$Python'. Install uv for that interpreter and try again."
    }
}

function Assert-PyProjectExists {
    if (-not (Test-Path -LiteralPath "pyproject.toml")) {
        throw "pyproject.toml is required for the uv setup flow."
    }
}

function Ensure-Venv {
    param(
        [string]$Python
    )

    if (Test-Path -LiteralPath ".venv") {
        Write-Step "📦 Reusing existing virtual environment at .venv" ([ConsoleColor]::DarkYellow)
        return
    }

    Write-Step "📦 Creating virtual environment with uv..." ([ConsoleColor]::Yellow)
    Invoke-PythonCommand -Python $Python -Arguments @("-m", "uv", "venv", ".venv")
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

Write-Step "🚀 Starting uv environment setup..." ([ConsoleColor]::Cyan)
Assert-PythonPath -Path $PythonPath

Write-Step "🐍 Validating Python interpreter..." ([ConsoleColor]::Yellow)
Invoke-PythonCommand -Python $PythonPath -Arguments @("--version")

Write-Step "🧰 Checking uv availability..." ([ConsoleColor]::Yellow)
Assert-UvAvailable -Python $PythonPath

Write-Step "📄 Checking uv project files..." ([ConsoleColor]::Yellow)
Assert-PyProjectExists

Ensure-Venv -Python $PythonPath

$syncArguments = Get-UvSyncArguments -SelectedProfile $Profile -UseDevDependencies:$useDevDependencies
$dependencyMode = if ($useDevDependencies) { "including dev dependencies" } else { "without dev dependencies" }

Write-Step "🔁 Syncing dependencies for profile '$Profile' ($dependencyMode)..." ([ConsoleColor]::Yellow)
Invoke-PythonCommand -Python $PythonPath -Arguments $syncArguments

$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"

Write-Step "✅ Environment setup completed successfully!" ([ConsoleColor]::Green)
Write-Host "Profile synced: $Profile"
Write-Host "Dev dependencies: $useDevDependencies"
Write-Host "Virtual environment: .venv"
Write-Host "Interpreter selection in VS Code remains manual."
Write-Host "Suggested interpreter path: $venvPython"
