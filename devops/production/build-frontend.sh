#!/bin/bash
set -e

echo "Building frontend application..."

# Build the frontend using Docker
docker build \
  --build-arg VITE_API_URL=https://florence-trees.fralo.dev/api \
  -f devops/production/Dockerfile.frontend \
  -t florence-trees-frontend-builder \
  ../../

# Create a temporary container and copy the built files
echo "Extracting built files..."
docker create --name temp-frontend florence-trees-frontend-builder
docker cp temp-frontend:/app/dist ./frontend_dist
docker rm temp-frontend

echo "Frontend built successfully! Files are in ./frontend_dist"
echo "You can now run: docker-compose up -d"
