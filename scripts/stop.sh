#!/usr/bin/env bash
set -euo pipefail

container_name="pm-mvp"

if docker ps -aq -f "name=^${container_name}$" | grep -q .; then
  docker rm -f "$container_name" >/dev/null
  echo "Stopped and removed container '${container_name}'."
else
  echo "Container '${container_name}' is not running."
fi