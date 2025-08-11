FROM python:3.9-slim

# Install system dependencies for opus and audio libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    libopus-dev \
    libsndfile1 \
    net-tools \
    procps \
    portaudio19-dev \
    python3-pyaudio \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and setup files first (better layer caching)
COPY requirements.txt setup.py ./

# Update pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir wheel && \
    # Install difficult packages first
    pip install --no-cache-dir PyAudio opuslib && \
    # Then install the rest
    pip install --no-cache-dir -r requirements.txt || \
    echo "Some packages failed to install, continuing anyway"

# Copy the rest of the application
COPY audionix_connect/ ./audionix_connect/
COPY config.json ./

# Install the package with --no-deps to avoid dependency errors
# We already installed the main dependencies earlier
RUN pip install -e . --no-deps

# Create volume mount point for configuration
VOLUME /config

# Expose UDP ports (adjust as needed for your specific use case)
EXPOSE 5004/udp
EXPOSE 5005/udp

# Copy healthcheck script
COPY docker-healthcheck.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-healthcheck.sh

# Set up healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD ["/usr/local/bin/docker-healthcheck.sh"]

# Command to run the application
CMD ["audionix-connect", "start", "--config", "/config/config.json"]
