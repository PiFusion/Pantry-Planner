$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

if (!(Test-Path ".venv")) {
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

flask --app pantry_planner init-db
flask --app pantry_planner sync-ingredients

$env:PYTHONPATH = "."
pytest -q

if ($args.Count -gt 0 -and $args[0] -eq "--serve") {
    flask --app pantry_planner run --debug
} else {
    Write-Host ""
    Write-Host "All setup + tests completed successfully."
    Write-Host "Start the app with:"
    Write-Host "  flask --app pantry_planner run --debug"
}
