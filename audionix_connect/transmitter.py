"""
Stream transmitter for outgoing audio streams.
"""

import socket
import struct
import time
import logging
import random
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RTPTransmitter:
    """Transmitter for RTP audio streams."""
    
    def __init__(self, destination_address: str, destination_port: int):
        """
        Initialize the RTP transmitter.
        
        Args:
            destination_address: Destination IP address
            destination_port: Destination UDP port
        """
        self.destination_address = destination_address
        self.destination_port = destination_port
        self.socket = None
        self.sequence_number = random.randint(0, 65535)
        self.timestamp = random.randint(0, 0xFFFFFFFF)
        self.ssrc = random.randint(0, 0xFFFFFFFF)  # Sender identifier
        self.payload_type = 96  # Dynamic payload type
        self.sample_rate = 48000
        self.running = False
    
    def start(self) -> None:
        """Start the transmitter."""
        if self.running:
            logger.warning("Transmitter already running")
            return
        
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.running = True
            logger.info(f"Transmitter started, sending to {self.destination_address}:{self.destination_port}")
        except Exception as e:
            self.running = False
            logger.error(f"Error starting transmitter: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the transmitter."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
    
    def create_rtp_packet(self, payload: bytes, marker: bool = False) -> bytes:
        """
        Create an RTP packet with the given payload.
        
        Args:
            payload: Audio payload data
            marker: Marker bit (typically used to mark first packet after silence)
            
        Returns:
            Complete RTP packet as bytes
        """
        # RTP header (12 bytes)
        version = 2  # RTP version 2
        padding = 0  # No padding
        extension = 0  # No extension
        csrc_count = 0  # No contributing sources
        
        # First byte: version (2 bits), padding (1 bit), extension (1 bit), CSRC count (4 bits)
        first_byte = (version << 6) | (padding << 5) | (extension << 4) | csrc_count
        
        # Second byte: marker (1 bit), payload type (7 bits)
        second_byte = (marker << 7) | self.payload_type
        
        # Create header
        header = struct.pack('!BBHII',
                            first_byte,
                            second_byte,
                            self.sequence_number,
                            self.timestamp,
                            self.ssrc)
        
        # Increment sequence number and timestamp
        self.sequence_number = (self.sequence_number + 1) % 65536
        # Timestamp increment depends on sample rate and frame duration
        # For 48kHz and 20ms frames: 48000 * 0.02 = 960 samples
        self.timestamp = (self.timestamp + 960) % (2**32)
        
        # Combine header and payload
        return header + payload
    
    def send(self, payload: bytes, marker: bool = False) -> bool:
        """
        Send an audio payload as an RTP packet.
        
        Args:
            payload: Audio payload data
            marker: Marker bit flag
            
        Returns:
            True if sending was successful, False otherwise
        """
        if not self.running or not self.socket:
            logger.error("Cannot send: transmitter not running")
            return False
        
        try:
            # Create RTP packet
            packet = self.create_rtp_packet(payload, marker)
            
            # Send packet
            self.socket.sendto(packet, (self.destination_address, self.destination_port))
            return True
        except Exception as e:
            logger.error(f"Error sending packet: {e}")
            return False


class PCMTransmitter(RTPTransmitter):
    """Specialized transmitter for PCM audio."""
    
    def __init__(self, destination_address: str, destination_port: int):
        """Initialize PCM transmitter."""
        super().__init__(destination_address, destination_port)
        self.payload_type = 97  # Dynamic payload type for PCM
        # PCM-specific initialization could go here


class OpusTransmitter(RTPTransmitter):
    """Specialized transmitter for Opus-encoded audio."""
    
    def __init__(self, destination_address: str, destination_port: int):
        """Initialize Opus transmitter."""
        super().__init__(destination_address, destination_port)
        self.payload_type = 98  # Dynamic payload type for Opus
        # Opus-specific initialization could go here


def create_transmitter(destination_address: str, destination_port: int, encoding: str) -> RTPTransmitter:
    """
    Factory function to create the appropriate transmitter.
    
    Args:
        destination_address: Destination IP address
        destination_port: Destination UDP port
        encoding: Audio encoding (pcm or opus)
        
    Returns:
        An RTPTransmitter instance for the specified encoding
        
    Raises:
        ValueError: If an unsupported encoding is specified
    """
    if encoding.lower() == "pcm":
        return PCMTransmitter(destination_address, destination_port)
    elif encoding.lower() == "opus":
        return OpusTransmitter(destination_address, destination_port)
    else:
        raise ValueError(f"Unsupported encoding: {encoding}")
