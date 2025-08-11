#!/bin/bash

# AudionixConnect installation script

echo "Installing AudionixConnect..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

echo "AudionixConnect has been installed successfully!"
echo
echo "To use AudionixConnect, activate the virtual environment:"
echo "  source venv/bin/activate"
echo
echo "Then run the application:"
echo "  audionix-connect start"
echo "  audionix-connect forward SOURCE_IP SOURCE_PORT DEST_IP DEST_PORT"
echo
echo "For more information, see the README.md file."
