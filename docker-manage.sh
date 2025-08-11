#!/bin/bash

# Helper script for managing AudionixConnect Docker deployment

# Function to display help message
show_help() {
  echo "AudionixConnect Docker Management Script"
  echo ""
  echo "Usage:"
  echo "  $0 [command]"
  echo ""
  echo "Commands:"
  echo "  build       Build the Docker image"
  echo "  rebuild     Completely rebuild the image without cache"
  echo "  up          Build if needed and start container (docker-compose up -d --build)"
  echo "  start       Start the AudionixConnect container"
  echo "  stop        Stop the AudionixConnect container"
  echo "  restart     Restart the AudionixConnect container"
  echo "  dev         Start in development mode with local code mounted"
  echo "  logs        Show container logs"
  echo "  status      Show container status"
  echo "  help        Show this help message"
}

# Build the Docker image
build() {
  echo "Building AudionixConnect Docker image..."
  docker-compose build
}

# Start the container
start() {
  echo "Starting AudionixConnect container..."
  docker-compose up -d
  echo "Container started. Use '$0 logs' to view logs."
}

# Stop the container
stop() {
  echo "Stopping AudionixConnect container..."
  docker-compose down
}

# Restart the container
restart() {
  echo "Restarting AudionixConnect container..."
  docker-compose restart
}

# Show container logs
logs() {
  docker-compose logs -f
}

# Show container status
status() {
  docker-compose ps
}

# Start in development mode
dev() {
  echo "Starting AudionixConnect in development mode..."
  docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
  echo "Development container started. Use '$0 logs' to view logs."
}

# Complete rebuild without cache
rebuild() {
  echo "Rebuilding AudionixConnect Docker container without cache..."
  docker-compose down
  docker rmi audionix-connect:latest || true
  docker image prune -f
  docker-compose build --no-cache
  echo "Build complete. To start the container, run '$0 start'"
}

# Docker-compose up with build
up() {
  echo "Building (if needed) and starting AudionixConnect container..."
  docker-compose up -d --build
  echo "Container started. Use '$0 logs' to view logs."
}

# Process command line arguments
case "$1" in
  build)
    build
    ;;
  rebuild)
    rebuild
    ;;
  up)
    up
    ;;
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    restart
    ;;
  dev)
    dev
    ;;
  logs)
    logs
    ;;
  status)
    status
    ;;
  help|--help|-h)
    show_help
    ;;
  *)
    # Default action if no arguments
    show_help
    ;;
esac
