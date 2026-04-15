#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${1:-face-recognition-service:latest}"
CONTAINER_NAME="face-recognition-service"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed on target host." >&2
  exit 1
fi

docker pull "$IMAGE_NAME"
docker stop "$CONTAINER_NAME" || true
docker rm "$CONTAINER_NAME" || true
docker run -d --name "$CONTAINER_NAME" -p 8000:8000 "$IMAGE_NAME"

echo "Deployment complete: $CONTAINER_NAME running on port 8000"
