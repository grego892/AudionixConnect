# AudionixConnect

A professional audio streaming management system for Livewire+ and AES67 audio networks. AudionixConnect provides a web-based interface for managing audio senders and receivers with real-time monitoring and control capabilities.

## Features

### Core Audio Processing
- **Multi-Protocol Support**: Livewire+ and AES67 protocol compatibility
- **Audio Formats**: PCM (16/24-bit) and Opus encoding support
- **Real-Time Processing**: 48kHz/24-bit audio with low-latency streaming
- **Multicast RTP**: Efficient multicast audio distribution
- **Audio Level Monitoring**: Real-time audio level meters with dB display

### Web Interface
- **Modern React Frontend**: Material-UI based responsive interface
- **Real-Time Updates**: WebSocket integration for live status updates
- **Comprehensive Management**: Full CRUD operations for senders and receivers
- **System Monitoring**: Detailed system status and diagnostics
- **Configuration Management**: JSON-based configuration with backup/restore

### System Architecture
- **Docker Containerized**: Easy deployment with Docker Compose
- **Scalable Backend**: Flask-based REST API with modular design
- **Network Aware**: Automatic network interface detection and validation
- **Production Ready**: Nginx reverse proxy with proper logging

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Ubuntu Server 20.04+ (recommended)
- Network interfaces supporting multicast

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd AudionixConnect
   ```

2. **Start the system:**
   ```bash
   docker-compose up -d
   ```

3. **Access the web interface:**
   - Open your browser to `http://localhost`
   - The system will automatically detect available network interfaces

### Configuration

The system uses JSON configuration files stored in `/app/config/`. Key configuration areas:

- **Audio Settings**: Sample rate, bit depth, channel configuration
- **Network Settings**: Interface selection, port ranges, multicast TTL
- **Protocol Settings**: Livewire+/AES67 specific configurations
- **Monitoring**: Update intervals and data retention settings

## Architecture Overview

### Backend Components

#### Main Application (`backend/app.py`)
- Flask application with WebSocket support
- Real-time monitoring loop for audio levels and system status
- API routing and error handling

#### Audio Processing (`backend/audio/`)
- **Stream Manager**: Core sender/receiver management
- **RTP Handler**: Packet processing for Livewire+/AES67
- **Audio Codec**: Format conversion and encoding
- **Audio Processor**: Level calculation and signal analysis

#### Configuration (`backend/config/`)
- **Config Manager**: JSON configuration management
- **Validation**: Configuration validation and defaults
- **Backup/Restore**: Configuration versioning

#### API Endpoints (`backend/api/`)
- **Sender API**: Sender management endpoints
- **Receiver API**: Receiver management endpoints  
- **Status API**: System monitoring endpoints

### Frontend Components

#### Core Application (`frontend/src/`)
- **App.js**: Main application with routing and state management
- **Socket Service**: WebSocket communication layer
- **API Service**: HTTP API client with error handling

#### User Interface (`frontend/src/components/`)
- **Dashboard**: System overview with real-time monitoring
- **Senders**: Sender management with audio level displays
- **Receivers**: Receiver management with statistics
- **Status**: Comprehensive system diagnostics
- **Settings**: Configuration management interface

## Development

### Backend Development

1. **Set up Python environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run development server:**
   ```bash
   python app.py
   ```

### Frontend Development

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm start
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

## Configuration Reference

### Audio Configuration
```json
{
  "audio": {
    "sample_rate": 48000,
    "bit_depth": 24,
    "channels": 2,
    "buffer_size": 1024
  }
}
```

### Network Configuration
```json
{
  "network": {
    "default_interface": "eth0",
    "multicast_ttl": 32,
    "rtp_port_range": {
      "start": 5004,
      "end": 5100
    }
  }
}
```

### Protocol Configuration
```json
{
  "protocols": {
    "livewire_plus": {
      "enabled": true,
      "channel_base": 32768
    },
    "aes67": {
      "enabled": true,
      "session_name": "AudionixConnect"
    }
  }
}
```

## API Reference

### Senders
- `GET /api/senders` - List all senders
- `POST /api/senders` - Create new sender
- `PUT /api/senders/{id}` - Update sender
- `DELETE /api/senders/{id}` - Delete sender
- `POST /api/senders/{id}/start` - Start sender
- `POST /api/senders/{id}/stop` - Stop sender

### Receivers
- `GET /api/receivers` - List all receivers
- `POST /api/receivers` - Create new receiver
- `PUT /api/receivers/{id}` - Update receiver
- `DELETE /api/receivers/{id}` - Delete receiver
- `POST /api/receivers/{id}/start` - Start receiver
- `POST /api/receivers/{id}/stop` - Stop receiver

### System
- `GET /api/status` - System status and statistics
- `GET /api/config` - Current configuration
- `PUT /api/config` - Update configuration
- `POST /api/config/reset` - Reset to defaults
- `GET /api/network/status` - Network interface status
- `POST /api/diagnostics/run` - Run system diagnostics

## WebSocket Events

### Client → Server
- `request_status` - Request current system status

### Server → Client
- `status_update` - System status update
- `audio_levels` - Real-time audio level data
- `sender_status_changed` - Sender status change
- `receiver_status_changed` - Receiver status change

## Deployment

### Production Deployment

1. **Prepare the system:**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Configure environment:**
   ```bash
   # Create production environment file
   cp .env.example .env
   # Edit .env with your production settings
   ```

3. **Deploy the application:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Security Considerations

- Change default passwords and API keys
- Configure firewall rules for RTP traffic
- Use HTTPS in production environments
- Regularly update container images
- Monitor system logs for security events

## Troubleshooting

### Common Issues

**Audio not flowing:**
- Check multicast routing: `ip route show`
- Verify interface supports multicast: `cat /sys/class/net/eth0/flags`
- Check firewall rules: `iptables -L`

**High latency:**
- Reduce buffer sizes in audio configuration
- Check network interface MTU settings
- Monitor CPU usage during peak load

**Connection issues:**
- Verify Docker container networking
- Check backend service health: `curl http://localhost:5000/api/status`
- Review container logs: `docker-compose logs`

### Logging

Application logs are available through Docker Compose:
```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Support

For technical support and feature requests:
- Review the troubleshooting section
- Check container logs for error messages
- Verify network configuration matches requirements

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Version History

- **v1.0.0** - Initial release
  - Core audio streaming functionality
  - Web-based management interface
  - Docker containerization
  - Livewire+ and AES67 support

- **Audio Stream Management**: Support for Livewire+ and AES67 audio streams (48kHz, 24-bit, UDP)
- **Flexible Audio Processing**: Uncompressed PCM or Opus-encoded audio transmission
- **Web-Based Interface**: Flask backend with Material UI frontend
- **Real-time Monitoring**: Audio level meters and status indicators
- **Network Diagnostics**: Connection status and error monitoring
- **Docker Support**: Fully containerized for Ubuntu Server deployment
- **Multi-instance Support**: Multiple concurrent Senders and Receivers

## Architecture

```
AudionixConnect/
├── backend/                 # Flask API and audio processing
│   ├── app.py              # Main Flask application
│   ├── audio/              # Audio processing modules
│   ├── api/                # REST API endpoints
│   ├── config/             # Configuration management
│   └── requirements.txt    # Python dependencies
├── frontend/               # Material UI React frontend
│   ├── src/                # React components
│   ├── public/             # Static assets
│   └── package.json        # Node.js dependencies
├── docker/                 # Docker configuration
├── configs/                # JSON configuration storage
└── docs/                   # Documentation
```

## Quick Start

1. **Prerequisites**:
   - Docker and Docker Compose
   - Ubuntu Server (recommended)
   - Network access to multicast audio streams

2. **Installation**:
   ```bash
   git clone <repository>
   cd AudionixConnect
   docker-compose up -d
   ```

3. **Access**:
   - Web Interface: http://localhost:3000
   - API Endpoints: http://localhost:5000/api

## Configuration

Audio streams and system settings are stored in JSON format in the `configs/` directory. The web interface provides full configuration management capabilities.

## Technical Specifications

- **Audio Format**: 48kHz, 24-bit, multicast RTP
- **Protocols**: Livewire+, AES67
- **Encoding**: PCM (uncompressed) or Opus
- **Transport**: UDP multicast (input), IP network (transmission)
- **Container**: Docker on Ubuntu Server

## License

Professional Audio Streaming System - All Rights Reserved
