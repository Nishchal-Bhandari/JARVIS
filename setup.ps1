$ErrorActionPreference = "Stop"

$pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $pythonLauncher) {
    & $pythonLauncher.Source -3 -m venv (Join-Path $PSScriptRoot ".venv")
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) {
        throw "Python 3.11 or newer is required. Install Python and ensure it is on PATH."
    }
    & $pythonCommand.Source -m venv (Join-Path $PSScriptRoot ".venv")
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $venvPython -m pip install -e "$(Join-Path $PSScriptRoot 'backend')[dev]"

Push-Location (Join-Path $PSScriptRoot "frontend")
try {
    npm ci
} finally {
    Pop-Location
}
