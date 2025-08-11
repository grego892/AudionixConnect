#!/bin/bash

# Script to rebuild the Docker container after dependency changes

echo "Rebuilding AudionixConnect Docker container..."

# Clean up old images
echo "Cleaning up old images..."
docker-compose down
docker rmi audionix-connect:latest || true

# Rebuild with no cache to ensure all dependencies are fresh
echo "Building fresh image..."
docker-compose build --no-cache

echo "Build complete. To start the container, run:"
echo "./docker-manage.sh start"
