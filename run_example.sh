#!/bin/bash

# Example script to run AudionixConnect

# Activate virtual environment
source venv/bin/activate

# Show version
audionix-connect version

# Start with default config
echo "Starting AudionixConnect with default config..."
echo "Press Ctrl+C to stop"
audionix-connect start

# You can also use the forward command to directly specify stream parameters:
# audionix-connect forward 239.192.0.1 5004 192.168.1.100 5005 --format aes67 --encoding opus
