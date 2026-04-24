$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion.Major -ge 7) {
  $PSNativeCommandUseErrorActionPreference = $true
}

function Test-DockerAvailable {
  try {
    docker info *> $null
    return $true
  } catch {
    return $false
  }
}

$containerName = "pm-mvp"

if (-not (Test-DockerAvailable)) {
  Write-Host "Docker daemon is not available. Nothing to stop."
  exit 0
}

$existingContainer = docker ps -aq -f "name=^${containerName}$"

if ($existingContainer) {
  docker rm -f $containerName | Out-Null
  Write-Host "Stopped and removed container '$containerName'."
} else {
  Write-Host "Container '$containerName' is not running."
}