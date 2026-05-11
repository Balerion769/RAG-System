Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\frontend"
try {
  npm start
}
finally {
  Pop-Location
}

