# Docker Deployment Guide for AudionixConnect

This guide explains how to run AudionixConnect in Docker using Docker Compose.

## Prerequisites

- Docker Engine installed (version 19.03.0+)
- Docker Compose installed (version 1.27.0+)
- Basic understanding of Docker and networking concepts

## Quick Start

1. Build and start the container:

```bash
./docker-manage.sh build
./docker-manage.sh start
```

2. Check the container status:

```bash
./docker-manage.sh status
```

3. View logs:

```bash
./docker-manage.sh logs
```

## Configuration

The configuration file is mounted from `./config/config.json` into the container. You can modify this file to change the input and output settings.

Example configuration:

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

After changing the configuration, restart the container:

```bash
./docker-manage.sh restart
```

## Network Considerations

### Host Network Mode

By default, the Docker Compose setup uses `network_mode: host` to ensure proper handling of multicast traffic. This gives the container direct access to the host's network interfaces, which is often required for receiving multicast streams.

### Using Bridge Networking

If you prefer not to use host networking, you can modify the `docker-compose.yml` file to use bridge networking with port mappings:

1. Comment out the `network_mode: host` line
2. Uncomment the `ports` section
3. Uncomment the `cap_add` section to add the `NET_ADMIN` capability

You may also need to configure the Docker daemon to enable multicast routing within bridge networks.

## Advanced Usage

### Custom Docker Images

To build a custom image with different base:

1. Modify the `Dockerfile` as needed
2. Rebuild the image:

```bash
docker-compose build --no-cache
```

### Multiple Instances

To run multiple instances:

1. Create multiple configuration files in the `config` directory
2. Create additional services in `docker-compose.yml`:

```yaml
services:
  audionix-connect-1:
    # ... (same as original)
    volumes:
      - ./config/config1.json:/config/config.json

  audionix-connect-2:
    # ... (same as original)
    volumes:
      - ./config/config2.json:/config/config.json
```

## Troubleshooting

1. **Cannot receive multicast streams**:

   - Verify that the host can receive multicast traffic
   - Check that the correct network interface is being used
   - Test with `tcpdump` on the host: `tcpdump -i <interface> udp port 5004`

2. **Container exits unexpectedly**:

   - Check the logs: `./docker-manage.sh logs`
   - Verify the configuration file is mounted correctly
   - Ensure all dependencies are installed in the Dockerfile

3. **High CPU/memory usage**:
   - Consider limiting resources in `docker-compose.yml`:
     ```yaml
     services:
       audionix-connect:
         # ... other configs
         deploy:
           resources:
             limits:
               cpus: "0.50"
               memory: 512M
     ```
