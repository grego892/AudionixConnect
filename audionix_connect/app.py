"""
Main application controller for AudionixConnect.
"""

import logging
import time
import threading
from typing import Optional, Dict, Any

from .config import Config, load_config
from .receiver import create_receiver, RTPPacket
from .processor import create_processor
from .transmitter import create_transmitter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AudionixConnect:
    """Main controller class for AudionixConnect application."""
    
    def __init__(self, config_path: str):
        """
        Initialize the application.
        
        Args:
            config_path: Path to the configuration JSON file
        """
        self.config_path = config_path
        self.config = None
        self.receiver = None
        self.processor = None
        self.transmitter = None
        self.running = False
        self.stats = {
            "packets_received": 0,
            "packets_sent": 0,
            "errors": 0,
            "start_time": 0,
        }
    
    def load_configuration(self) -> None:
        """Load and validate the configuration."""
        try:
            self.config = load_config(self.config_path)
            logger.info(f"Configuration loaded from {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def initialize_components(self) -> None:
        """Initialize the stream components based on the configuration."""
        if not self.config:
            raise ValueError("Configuration not loaded")
        
        try:
            # Create receiver for the input stream
            self.receiver = create_receiver(
                self.config.input.multicast_address,
                self.config.input.port,
                self.config.input.format
            )
            logger.info(f"Receiver initialized for {self.config.input.format} stream")
            
            # Create audio processor
            self.processor = create_processor(
                self.config.output.encoding,
                self.config.output.bitrate
            )
            logger.info(f"Audio processor initialized for {self.config.output.encoding} encoding")
            
            # Create transmitter for the output stream
            self.transmitter = create_transmitter(
                self.config.output.destination_address,
                self.config.output.destination_port,
                self.config.output.encoding
            )
            logger.info("Transmitter initialized")
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def handle_packet(self, packet: RTPPacket) -> None:
        """
        Handle received RTP packets.
        
        Args:
            packet: The received RTP packet
        """
        try:
            # Process the packet and get the audio data
            audio_data = self.processor.process_packet(packet.payload)
            
            # If audio data was successfully processed
            if audio_data.size > 0:
                # Prepare the outgoing payload
                output_payload = self.processor.prepare_payload(audio_data)
                
                # Send the packet
                if output_payload:
                    success = self.transmitter.send(output_payload, packet.marker)
                    if success:
                        self.stats["packets_sent"] += 1
            
            self.stats["packets_received"] += 1
        except Exception as e:
            logger.error(f"Error handling packet: {e}")
            self.stats["errors"] += 1
    
    def start(self) -> None:
        """Start the audio stream processing."""
        if self.running:
            logger.warning("AudionixConnect is already running")
            return
        
        try:
            logger.info("Starting AudionixConnect")
            
            # Load configuration if not already loaded
            if not self.config:
                self.load_configuration()
            
            # Initialize components if not already initialized
            if not self.receiver or not self.processor or not self.transmitter:
                self.initialize_components()
            
            # Reset statistics
            self.stats = {
                "packets_received": 0,
                "packets_sent": 0,
                "errors": 0,
                "start_time": time.time(),
            }
            
            # Start the transmitter
            self.transmitter.start()
            
            # Start the receiver with our packet handler
            self.running = True
            
            # Start the statistics reporter in a separate thread
            self.stats_thread = threading.Thread(target=self._report_stats)
            self.stats_thread.daemon = True
            self.stats_thread.start()
            
            # Start the receiver (this will block until stop is called)
            self.receiver.start(self.handle_packet)
        except Exception as e:
            self.running = False
            logger.error(f"Error starting AudionixConnect: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the audio stream processing."""
        if not self.running:
            logger.warning("AudionixConnect is not running")
            return
        
        try:
            logger.info("Stopping AudionixConnect")
            self.running = False
            
            # Stop the receiver
            if self.receiver:
                self.receiver.stop()
            
            # Stop the transmitter
            if self.transmitter:
                self.transmitter.stop()
            
            # Final statistics report
            self._print_stats()
        except Exception as e:
            logger.error(f"Error stopping AudionixConnect: {e}")
    
    def _report_stats(self) -> None:
        """Periodically report statistics."""
        while self.running:
            self._print_stats()
            time.sleep(10)  # Report every 10 seconds
    
    def _print_stats(self) -> None:
        """Print current statistics."""
        if self.stats["start_time"] == 0:
            return
        
        elapsed = time.time() - self.stats["start_time"]
        if elapsed == 0:
            return
        
        rx_rate = self.stats["packets_received"] / elapsed
        tx_rate = self.stats["packets_sent"] / elapsed
        error_rate = self.stats["errors"] / max(1, self.stats["packets_received"]) * 100
        
        logger.info(
            f"Stats: Received {self.stats['packets_received']} packets ({rx_rate:.1f}/s), "
            f"Sent {self.stats['packets_sent']} packets ({tx_rate:.1f}/s), "
            f"Errors: {self.stats['errors']} ({error_rate:.2f}%)"
        )
