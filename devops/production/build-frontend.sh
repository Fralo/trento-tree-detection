#!/bin/bash
set -e

echo "Building frontend application..."

# Get the project root directory (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Build the frontend using Docker
docker build \
  --build-arg VITE_API_URL=https://florence-trees.fralo.dev/api \
  -f "$SCRIPT_DIR/Dockerfile.frontend" \
  -t florence-trees-frontend-builder \
  "$PROJECT_ROOT"

# Create a temporary container and copy the built files
echo "Extracting built files..."
docker create --name temp-frontend florence-trees-frontend-builder
docker cp temp-frontend:/app/dist ./frontend_dist
docker rm temp-frontend

echo "Frontend built successfully! Files are in ./frontend_dist"
echo "You can now run: docker-compose up -d"
