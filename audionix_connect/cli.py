"""
Command-line interface for AudionixConnect.
"""

import os
import sys
import click
import json
import logging
import signal
from pathlib import Path

from .app import AudionixConnect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration file path
DEFAULT_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".audionix_connect", "config.json")


def create_default_config() -> str:
    """
    Create a default configuration file if none exists.
    
    Returns:
        Path to the created config file
    """
    config_dir = os.path.dirname(DEFAULT_CONFIG_PATH)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    if not os.path.exists(DEFAULT_CONFIG_PATH):
        default_config = {
            "input": {
                "multicast_address": "239.192.0.1",
                "port": 5004,
                "format": "aes67"
            },
            "output": {
                "destination_address": "127.0.0.1",
                "destination_port": 5005,
                "encoding": "opus",
                "bitrate": 128000
            }
        }
        
        with open(DEFAULT_CONFIG_PATH, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"Created default configuration at {DEFAULT_CONFIG_PATH}")
    
    return DEFAULT_CONFIG_PATH


def handle_signals(app: AudionixConnect) -> None:
    """
    Set up signal handlers for graceful shutdown.
    
    Args:
        app: The AudionixConnect application instance
    """
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal, stopping...")
        app.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


@click.group()
def cli():
    """AudionixConnect - Stream audio over IP networks."""
    pass


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Path to configuration file')
def start(config):
    """Start the AudionixConnect service."""
    # Use provided config or default
    config_path = config if config else create_default_config()
    
    try:
        # Create and start the application
        app = AudionixConnect(config_path)
        
        # Set up signal handlers
        handle_signals(app)
        
        # Load configuration
        app.load_configuration()
        
        # Initialize components
        app.initialize_components()
        
        # Start processing
        logger.info("Starting AudionixConnect...")
        app.start()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('input_address', type=str)
@click.argument('input_port', type=int)
@click.argument('output_address', type=str)
@click.argument('output_port', type=int)
@click.option('--format', '-f', type=click.Choice(['aes67', 'livewire']), 
              default='aes67', help='Input stream format')
@click.option('--encoding', '-e', type=click.Choice(['pcm', 'opus']), 
              default='opus', help='Output encoding')
@click.option('--bitrate', '-b', type=int, default=128000, 
              help='Bitrate for Opus encoding (ignored for PCM)')
@click.option('--save-config', '-s', is_flag=True, 
              help='Save these settings as the default configuration')
def forward(input_address, input_port, output_address, output_port, 
           format, encoding, bitrate, save_config):
    """
    Forward audio from INPUT_ADDRESS:INPUT_PORT to OUTPUT_ADDRESS:OUTPUT_PORT.
    
    Example:
        audionix-connect forward 239.192.0.1 5004 192.168.1.100 5005 --format aes67 --encoding opus
    """
    # Create config dictionary
    config = {
        "input": {
            "multicast_address": input_address,
            "port": input_port,
            "format": format
        },
        "output": {
            "destination_address": output_address,
            "destination_port": output_port,
            "encoding": encoding,
            "bitrate": bitrate if encoding == "opus" else None
        }
    }
    
    # Save configuration if requested
    if save_config:
        config_dir = os.path.dirname(DEFAULT_CONFIG_PATH)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        with open(DEFAULT_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved configuration to {DEFAULT_CONFIG_PATH}")
    
    # Create a temporary config file
    temp_config_path = os.path.join(os.path.dirname(DEFAULT_CONFIG_PATH), "temp_config.json")
    with open(temp_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    try:
        # Create and start the application
        app = AudionixConnect(temp_config_path)
        
        # Set up signal handlers
        handle_signals(app)
        
        # Start processing
        logger.info("Starting AudionixConnect in forwarding mode...")
        app.start()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    finally:
        # Clean up temporary config file
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


@cli.command()
def version():
    """Display version information."""
    from . import __version__
    click.echo(f"AudionixConnect v{__version__}")


def main():
    """Main entry point for the application."""
    cli()


if __name__ == '__main__':
    main()
