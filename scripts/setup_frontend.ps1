Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\frontend"
try {
  npm install
}
finally {
  Pop-Location
}

