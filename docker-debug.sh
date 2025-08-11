#!/bin/bash

# Debug helper script for AudionixConnect Docker container

# Function to display help message
show_help() {
  echo "AudionixConnect Docker Debugging Helper"
  echo ""
  echo "Usage:"
  echo "  $0 [command]"
  echo ""
  echo "Commands:"
  echo "  shell      Launch a shell inside the running container"
  echo "  inspect    Inspect the container configuration"
  echo "  network    Show network interfaces and multicast info"
  echo "  packages   List installed Python packages"
  echo "  logs       Show container logs with timestamps"
  echo "  help       Show this help message"
}

# Check if container is running
check_container() {
  if ! docker ps | grep -q audionix-connect; then
    echo "Error: AudionixConnect container is not running."
    echo "Start the container with: ./docker-manage.sh start"
    exit 1
  fi
}

# Launch shell inside container
shell() {
  check_container
  echo "Launching shell inside AudionixConnect container..."
  docker exec -it audionix-connect /bin/bash
}

# Inspect container
inspect() {
  check_container
  echo "Inspecting AudionixConnect container..."
  docker inspect audionix-connect
}

# Show network info
network() {
  check_container
  echo "Network interfaces inside container:"
  docker exec -it audionix-connect ip addr show
  
  echo -e "\nMulticast routes inside container:"
  docker exec -it audionix-connect ip mroute show
  
  echo -e "\nListening ports inside container:"
  docker exec -it audionix-connect netstat -tuln
}

# List installed packages
packages() {
  check_container
  echo "Installed Python packages in container:"
  docker exec -it audionix-connect pip list
}

# Show logs with timestamps
logs() {
  check_container
  echo "Container logs with timestamps:"
  docker logs -t audionix-connect
}

# Process command line arguments
case "$1" in
  shell)
    shell
    ;;
  inspect)
    inspect
    ;;
  network)
    network
    ;;
  packages)
    packages
    ;;
  logs)
    logs
    ;;
  help|--help|-h)
    show_help
    ;;
  *)
    # Default action if no arguments
    show_help
    ;;
esac
