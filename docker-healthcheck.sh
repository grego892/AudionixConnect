#!/bin/bash

# Health check script for AudionixConnect Docker container
# This will be used by Docker's HEALTHCHECK directive

# Check if the process is running
if ! pgrep -f "audionix-connect start" > /dev/null; then
  echo "AudionixConnect process not found"
  exit 1
fi

# Check if the receiver is listening on the specified port
# Extract port from config file
PORT=$(grep -o '"port": [0-9]*' /config/config.json | awk '{print $2}')

# If we couldn't extract the port, use default
if [ -z "$PORT" ]; then
  PORT=5004
fi

# Check if the port is open
if ! netstat -tuln | grep -q ":$PORT"; then
  echo "AudionixConnect not listening on port $PORT"
  exit 1
fi

# All checks passed
echo "AudionixConnect is healthy"
exit 0
