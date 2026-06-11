param(
    [string]$PythonPath,
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

function New-CommandSpec {
    param(
        [string]$Command,
        [string[]]$BaseArguments,
        [string]$Description
    )

    return [pscustomobject]@{
        Command       = $Command
        BaseArguments = $BaseArguments
        Description   = $Description
    }
}

function Test-CommandSpec {
    param(
        [pscustomobject]$CommandSpec
    )

    $hasNativePreference = Test-Path Variable:\PSNativeCommandUseErrorActionPreference
    if ($hasNativePreference) {
        $previousNativePreference = $PSNativeCommandUseErrorActionPreference
        $PSNativeCommandUseErrorActionPreference = $false
    }

    try {
        & $CommandSpec.Command @($CommandSpec.BaseArguments + @("--version")) *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
    finally {
        if ($hasNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $previousNativePreference
        }
    }
}

function Resolve-PythonCommand {
    param(
        [string]$ExplicitPythonPath
    )

    $attemptedResolvers = @()

    if ($ExplicitPythonPath) {
        $attemptedResolvers += "explicit path '$ExplicitPythonPath'"
        Assert-PythonPath -Path $ExplicitPythonPath
        $pythonCommand = New-CommandSpec -Command $ExplicitPythonPath -BaseArguments @() -Description "explicit path '$ExplicitPythonPath'"
        if (-not (Test-CommandSpec -CommandSpec $pythonCommand)) {
            throw "Python at '$ExplicitPythonPath' did not respond correctly."
        }
        return $pythonCommand
    }

    $candidates = @(
        (New-CommandSpec -Command "py" -BaseArguments @("-3") -Description "py -3"),
        (New-CommandSpec -Command "python" -BaseArguments @() -Description "python from PATH")
    )

    foreach ($candidate in $candidates) {
        $attemptedResolvers += $candidate.Description
        if (Test-CommandSpec -CommandSpec $candidate) {
            return $candidate
        }
    }

    $attemptedText = $attemptedResolvers -join ", "
    throw "Unable to resolve a working Python interpreter. Tried: $attemptedText. Install/configure Python or pass -PythonPath."
}

function Invoke-CommandSpec {
    param(
        [pscustomobject]$CommandSpec,
        [string[]]$Arguments,
        [hashtable]$Environment = @{}
    )

    $allArguments = @($CommandSpec.BaseArguments + $Arguments)
    $previousValues = @{}

    try {
        foreach ($entry in $Environment.GetEnumerator()) {
            $name = [string]$entry.Key
            if (Test-Path "Env:$name") {
                $previousValues[$name] = (Get-Item "Env:$name").Value
            }
            else {
                $previousValues[$name] = $null
            }
            Set-Item -Path "Env:$name" -Value ([string]$entry.Value)
        }

        & $CommandSpec.Command @allArguments
        if ($LASTEXITCODE -ne 0) {
            $joinedArguments = $allArguments -join " "
            throw "Command failed: $($CommandSpec.Command) $joinedArguments"
        }
    }
    finally {
        foreach ($entry in $Environment.GetEnumerator()) {
            $name = [string]$entry.Key
            $previousValue = $previousValues[$name]
            if ($null -eq $previousValue) {
                Remove-Item "Env:$name" -ErrorAction SilentlyContinue
            }
            else {
                Set-Item -Path "Env:$name" -Value $previousValue
            }
        }
    }
}

function Resolve-UvCommand {
    param(
        [pscustomobject]$PythonCommand
    )

    $attemptedResolvers = @()
    $candidates = @(
        (New-CommandSpec -Command $PythonCommand.Command -BaseArguments @($PythonCommand.BaseArguments + @("-m", "uv")) -Description "uv module via $($PythonCommand.Description)"),
        (New-CommandSpec -Command "uv" -BaseArguments @() -Description "uv from PATH")
    )

    foreach ($candidate in $candidates) {
        $attemptedResolvers += $candidate.Description
        if (Test-CommandSpec -CommandSpec $candidate) {
            return $candidate
        }
    }

    $attemptedText = $attemptedResolvers -join ", "
    throw "Unable to resolve uv. Tried: $attemptedText. Install uv for the selected Python interpreter or expose uv.exe in PATH."
}

function Assert-PyProjectExists {
    if (-not (Test-Path -LiteralPath "pyproject.toml")) {
        throw "pyproject.toml is required for the uv setup flow."
    }
}

function Ensure-Venv {
    param(
        [pscustomobject]$UvCommand
    )

    if (Test-Path -LiteralPath ".venv") {
        Write-Step "[Environment] Reusing existing virtual environment at .venv" ([ConsoleColor]::DarkYellow)
        return
    }

    Write-Step "[Environment] Creating virtual environment with uv..." ([ConsoleColor]::Yellow)
    Invoke-CommandSpec -CommandSpec $UvCommand -Arguments @("venv", ".venv")
}

function Get-UvSyncEnvironment {
    $repoRoot = (Get-Location).Path
    $existingLinkMode = $env:UV_LINK_MODE

    if ($existingLinkMode) {
        return @{}
    }

    if ($repoRoot -like "*OneDrive*") {
        Write-Step "[uv] OneDrive path detected. Forcing UV_LINK_MODE=copy to avoid Windows hardlink errors." ([ConsoleColor]::DarkYellow)
        return @{ UV_LINK_MODE = "copy" }
    }

    return @{}
}

Write-Step "Starting uv environment setup for this repository." ([ConsoleColor]::Cyan)

Write-Phase "Phase 1: Resolve Python"
$pythonCommand = Resolve-PythonCommand -ExplicitPythonPath $PythonPath
Write-Step "[Python] Using interpreter resolved via $($pythonCommand.Description)." ([ConsoleColor]::DarkCyan)

Write-Step "[Python] Validating the selected Python interpreter..." ([ConsoleColor]::Yellow)
Invoke-CommandSpec -CommandSpec $pythonCommand -Arguments @("--version")

Write-Phase "Phase 2: Validate Tooling"
Write-Step "[uv] Checking whether uv is available for the selected interpreter..." ([ConsoleColor]::Yellow)
$uvCommand = Resolve-UvCommand -PythonCommand $pythonCommand
Write-Step "[uv] Using $($uvCommand.Description)." ([ConsoleColor]::DarkCyan)

Write-Step "[Project] Verifying that pyproject.toml is available..." ([ConsoleColor]::Yellow)
Assert-PyProjectExists

Write-Phase "Phase 3: Prepare Environment"
Ensure-Venv -UvCommand $uvCommand

$syncArguments = @("scripts/run_uv_sync.py", "init")
if ($useDevDependencies) {
    $syncArguments += "--include-dev"
}
else {
    $syncArguments += "--no-dev"
}
$dependencyMode = if ($useDevDependencies) { "including dev dependencies" } else { "without dev dependencies" }

Write-Phase "Phase 4: Sync Dependencies"
Write-Step "[Dependencies] Syncing the active YAML profile ($dependencyMode)..." ([ConsoleColor]::Yellow)
Invoke-CommandSpec -CommandSpec $pythonCommand -Arguments $syncArguments

$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"

Write-Phase "Phase 5: Summary"
Write-Step "Environment setup completed successfully." ([ConsoleColor]::Green)
Write-Host "Profile synced: .template-profile.yaml"
Write-Host "Dev dependencies enabled: $useDevDependencies"
Write-Host "Virtual environment path: .venv"
Write-Host "VS Code interpreter selection remains a manual step."
Write-Host "Suggested interpreter path: $venvPython"
