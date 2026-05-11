Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\backend"
try {
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  pip install -e ".[dev,adk,rag,multimodal]"
  if (-not (Test-Path ".env")) {
    Copy-Item "..\.env.example" ".env"
  }
}
finally {
  Pop-Location
}

