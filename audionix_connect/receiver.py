"""
Stream receiver for multicast RTP audio streams.
"""

import socket
import struct
import logging
from typing import Optional, Tuple, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RTPPacket:
    """Basic RTP packet parser."""
    
    def __init__(self, packet_data: bytes):
        """
        Parse an RTP packet.
        
        Args:
            packet_data: Raw packet data
        """
        if len(packet_data) < 12:
            raise ValueError("Packet too short to be an RTP packet")
        
        # Parse RTP header (first 12 bytes)
        header = packet_data[:12]
        self.version = (header[0] >> 6) & 0x03
        self.padding = (header[0] >> 5) & 0x01
        self.extension = (header[0] >> 4) & 0x01
        self.csrc_count = header[0] & 0x0F
        self.marker = (header[1] >> 7) & 0x01
        self.payload_type = header[1] & 0x7F
        self.sequence_number = struct.unpack('!H', header[2:4])[0]
        self.timestamp = struct.unpack('!I', header[4:8])[0]
        self.ssrc = struct.unpack('!I', header[8:12])[0]
        
        # CSRC identifiers (if any)
        self.csrc = []
        for i in range(self.csrc_count):
            offset = 12 + i * 4
            if len(packet_data) >= offset + 4:
                self.csrc.append(struct.unpack('!I', packet_data[offset:offset+4])[0])
        
        # Payload starts after header and CSRC identifiers
        payload_offset = 12 + (self.csrc_count * 4)
        self.payload = packet_data[payload_offset:]
    
    def __str__(self) -> str:
        return f"RTP Packet: seq={self.sequence_number}, ts={self.timestamp}, pt={self.payload_type}"


class StreamReceiver:
    """Receiver for multicast RTP streams."""
    
    def __init__(self, multicast_address: str, port: int, format_type: str):
        """
        Initialize the stream receiver.
        
        Args:
            multicast_address: Multicast group address
            port: UDP port number
            format_type: Stream format type (livewire or aes67)
        """
        self.multicast_address = multicast_address
        self.port = port
        self.format_type = format_type
        self.socket = None
        self.running = False
        self.packet_handler = None
        
    def start(self, packet_handler: Callable[[RTPPacket], None]) -> None:
        """
        Start receiving the multicast stream.
        
        Args:
            packet_handler: Callback function to handle received RTP packets
        """
        if self.running:
            logger.warning("Receiver already running")
            return
        
        self.packet_handler = packet_handler
        self.running = True
        
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to port
            self.socket.bind(('', self.port))
            
            # Join multicast group
            mreq = struct.pack('4sl', socket.inet_aton(self.multicast_address), socket.INADDR_ANY)
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            logger.info(f"Listening for {self.format_type} stream on {self.multicast_address}:{self.port}")
            
            # Start receiving packets
            self._receive_loop()
        except Exception as e:
            self.running = False
            logger.error(f"Error starting receiver: {e}")
            raise
    
    def stop(self) -> None:
        """Stop receiving the multicast stream."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
    
    def _receive_loop(self) -> None:
        """Main receive loop."""
        self.socket.settimeout(0.5)  # 500ms timeout for clean shutdown
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(2048)  # Buffer size for UDP packets
                if data and self.packet_handler:
                    try:
                        packet = RTPPacket(data)
                        self.packet_handler(packet)
                    except Exception as e:
                        logger.error(f"Error processing packet: {e}")
            except socket.timeout:
                continue  # Just a timeout for checking self.running
            except Exception as e:
                if self.running:  # Only log if we're still supposed to be running
                    logger.error(f"Error in receive loop: {e}")


class LivewireReceiver(StreamReceiver):
    """Specialized receiver for Livewire streams."""
    
    def __init__(self, multicast_address: str, port: int):
        """Initialize Livewire receiver."""
        super().__init__(multicast_address, port, "livewire")
        # Livewire-specific initialization could go here


class AES67Receiver(StreamReceiver):
    """Specialized receiver for AES67 streams."""
    
    def __init__(self, multicast_address: str, port: int):
        """Initialize AES67 receiver."""
        super().__init__(multicast_address, port, "aes67")
        # AES67-specific initialization could go here


def create_receiver(multicast_address: str, port: int, format_type: str) -> StreamReceiver:
    """
    Factory function to create the appropriate receiver.
    
    Args:
        multicast_address: Multicast group address
        port: UDP port number
        format_type: Stream format type (livewire or aes67)
        
    Returns:
        A StreamReceiver instance for the specified format
        
    Raises:
        ValueError: If an unsupported format is specified
    """
    if format_type.lower() == "livewire":
        return LivewireReceiver(multicast_address, port)
    elif format_type.lower() == "aes67":
        return AES67Receiver(multicast_address, port)
    else:
        raise ValueError(f"Unsupported format: {format_type}")
