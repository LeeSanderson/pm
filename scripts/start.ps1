$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion.Major -ge 7) {
  $PSNativeCommandUseErrorActionPreference = $true
}

function Assert-DockerAvailable {
  try {
    docker info *> $null
  } catch {
    throw "Docker daemon is not available. Start Docker Desktop and retry."
  }
}

$repoRoot = Split-Path $PSScriptRoot -Parent
$imageName = "pm-mvp"
$containerName = "pm-mvp"
$envFilePath = Join-Path $repoRoot ".env"

Assert-DockerAvailable

$existingContainer = docker ps -aq -f "name=^${containerName}$"
if ($existingContainer) {
  docker rm -f $containerName | Out-Null
}

docker build -t $imageName $repoRoot

$runArgs = @(
  "run"
  "--detach"
  "--name"
  $containerName
  "-p"
  "8000:8000"
)

if (Test-Path $envFilePath) {
  $runArgs += @("--env-file", $envFilePath)
}

$runArgs += $imageName
docker @runArgs | Out-Null

Write-Host "App is starting at http://localhost:8000"