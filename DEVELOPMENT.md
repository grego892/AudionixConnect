# AudionixConnect Development Guide

This document provides an overview of the AudionixConnect project structure and development information.

## Project Overview

AudionixConnect is a Python application designed to:

1. Ingest multicast RTP audio streams (Livewire+ or AES67 format)
2. Process the audio (48kHz, 24-bit)
3. Forward the stream over IP networks using either uncompressed PCM or Opus-encoded audio

## Project Structure

```
AudionixConnect/
├── audionix_connect/         # Main package
│   ├── __init__.py           # Package initialization
│   ├── app.py                # Main application controller
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Configuration handling
│   ├── processor.py          # Audio processing
│   ├── receiver.py           # RTP stream receiver
│   └── transmitter.py        # RTP stream transmitter
├── tests/                    # Test directory
│   └── test_config.py        # Configuration tests
├── config.json               # Example configuration
├── install.sh                # Installation script
├── requirements.txt          # Python dependencies
├── run_example.sh            # Example run script
└── setup.py                  # Package setup script
```

## Core Components

### Configuration (config.py)

Handles loading and validating configuration from JSON files using Pydantic models.

### Receiver (receiver.py)

- `StreamReceiver`: Base class for receiving multicast RTP streams
- `LivewireReceiver`: Specialized receiver for Livewire streams
- `AES67Receiver`: Specialized receiver for AES67 streams

### Audio Processor (processor.py)

- `AudioProcessor`: Base class for audio processing
- `PCMProcessor`: Processor for uncompressed PCM audio
- `OpusProcessor`: Processor for Opus-encoded audio

### Transmitter (transmitter.py)

- `RTPTransmitter`: Base class for sending RTP packets
- `PCMTransmitter`: Specialized transmitter for PCM audio
- `OpusTransmitter`: Specialized transmitter for Opus-encoded audio

### Main Application (app.py)

`AudionixConnect` class orchestrates the components:

1. Loads configuration
2. Initializes stream components
3. Processes incoming packets
4. Forwards processed audio to destination

### Command-Line Interface (cli.py)

Provides a user-friendly CLI with commands:

- `start`: Start the service with a config file
- `forward`: Direct stream forwarding with specified parameters
- `version`: Display version information

## Configuration Format

```json
{
  "input": {
    "multicast_address": "239.192.0.1",
    "port": 5004,
    "format": "aes67" // or "livewire"
  },
  "output": {
    "destination_address": "192.168.1.100",
    "destination_port": 5005,
    "encoding": "opus", // or "pcm"
    "bitrate": 128000 // required for opus
  }
}
```

## Usage

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/AudionixConnect.git
cd AudionixConnect

# Run the installation script
./install.sh
```

### Running

```bash
# Activate the virtual environment
source venv/bin/activate

# Start with default config
audionix-connect start

# Start with custom config
audionix-connect start --config my_config.json

# Direct forwarding
audionix-connect forward 239.192.0.1 5004 192.168.1.100 5005 --format aes67 --encoding opus
```

## Development

### Adding Dependencies

Add new dependencies to `requirements.txt` and `setup.py`.

### Running Tests

```bash
pytest tests/
```

### Future Improvements

1. Add more robust error handling and recovery
2. Implement audio level monitoring
3. Add web-based dashboard for monitoring
4. Support for more audio codecs
5. Add multistream support (handling multiple streams simultaneously)

## Common Issues

1. **ImportError for dependencies**: Make sure all dependencies are installed. Some packages like `opuslib` might require additional system libraries.

2. **Permission denied for multicast**: The application may need elevated permissions to join multicast groups on some systems.

3. **Audio sync issues**: Check for proper handling of RTP timestamps in both receiver and transmitter.
