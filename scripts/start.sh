#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
image_name="pm-mvp"
container_name="pm-mvp"

if docker ps -aq -f "name=^${container_name}$" | grep -q .; then
  docker rm -f "$container_name" >/dev/null
fi

docker build -t "$image_name" "$repo_root"
docker run --detach --name "$container_name" -p 8000:8000 "$image_name" >/dev/null

echo "App is starting at http://localhost:8000"