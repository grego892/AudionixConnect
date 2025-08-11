# AudionixConnect

AudionixConnect is a Python application for ingesting multicast RTP audio streams (Livewire+ or AES67 format) and forwarding them over IP networks with either uncompressed PCM or Opus-encoded audio.

## Features

- Ingest multicast RTP audio streams (Livewire+ or AES67 format)
- 48kHz, 24-bit audio support
- Forward streams over IP using uncompressed PCM or Opus encoding
- Configuration via JSON files
- Reliable network streaming with error handling

## Installation

```bash
pip install -r requirements.txt
python setup.py install
```

## Usage

```bash
# Run with default config file
audionix-connect

# Specify custom config file
audionix-connect --config my_config.json
```

## Configuration

Create a JSON configuration file with your stream settings:

```json
{
  "input": {
    "multicast_address": "239.192.0.1",
    "port": 5004,
    "format": "aes67"
  },
  "output": {
    "destination_address": "192.168.1.100",
    "destination_port": 5005,
    "encoding": "opus",
    "bitrate": 128000
  }
}
```
