# AudionixConnect Docker Quick Reference

## Basic Commands

Build the Docker image:

```bash
./docker-manage.sh build
```

Start the container:

```bash
./docker-manage.sh start
```

View logs:

```bash
./docker-manage.sh logs
```

Check container status:

```bash
./docker-manage.sh status
```

Stop the container:

```bash
./docker-manage.sh stop
```

## Development Mode

Start in development mode (mounts local code):

```bash
./docker-manage.sh dev
```

## Configuration

The configuration files are located in the `./config/` directory:

- `config.json`: Default configuration
- `local-test.json`: Configuration for local testing

## Docker Compose Manual Commands

For more control, you can use Docker Compose directly:

```bash
# Start container
docker-compose up -d

# Stop container
docker-compose down

# Show logs
docker-compose logs -f

# Build with no cache
docker-compose build --no-cache
```

For development with code mounting:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```
