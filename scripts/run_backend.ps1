Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\backend"
try {
  .\.venv\Scripts\Activate.ps1
  $env:PYTHONUTF8 = "1"
  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
}
finally {
  Pop-Location
}

