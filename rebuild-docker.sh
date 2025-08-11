#!/bin/bash

# Script to rebuild the Docker container after dependency changes

echo "Rebuilding AudionixConnect Docker container..."

# Clean up old containers and images
echo "Cleaning up old containers and images..."
docker-compose down
docker rmi audionix-connect:latest || true

# Remove any dangling images that might have been created from failed builds
echo "Cleaning up any dangling images..."
docker image prune -f

# Rebuild with no cache to ensure all dependencies are fresh
echo "Building fresh image..."
docker-compose build --no-cache

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Build completed successfully."
    echo "To start the container, run:"
    echo "./docker-manage.sh start"
else
    echo "Build failed. Check the error messages above."
    exit 1
fi
