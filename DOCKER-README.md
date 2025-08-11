# Docker Implementation for AudionixConnect

The following Docker-related files have been added to your AudionixConnect project:

## Core Docker Files

- `Dockerfile`: Contains instructions for building the Docker image
- `docker-compose.yml`: Configuration for deploying the container
- `docker-compose.dev.yml`: Override for development environments
- `docker-healthcheck.sh`: Script for Docker health checks

## Configuration

- `config/config.json`: Main configuration file used by the container
- `config/local-test.json`: Alternative configuration for local testing

## Management Tools

- `docker-manage.sh`: Helper script for common Docker operations
- `DOCKER.md`: Comprehensive Docker deployment guide
- `DOCKER-QUICKREF.md`: Quick reference for Docker commands

## Implementation Details

1. **Base Image**: Uses Python 3.9 slim with necessary system libraries
2. **Networking**: Set up for host networking to support multicast
3. **Configuration**: External config mounted from host
4. **Health Check**: Monitors application status
5. **Development Mode**: Support for code mounting and debugging

## Next Steps

1. Build the Docker image:

   ```
   ./docker-manage.sh build
   ```

2. Start the container:

   ```
   ./docker-manage.sh start
   ```

3. Verify the container is running:

   ```
   ./docker-manage.sh status
   ```

4. Check the logs for proper operation:

   ```
   ./docker-manage.sh logs
   ```

5. If needed, adjust the configuration in `config/config.json`

For more detailed information, please refer to the `DOCKER.md` document.
