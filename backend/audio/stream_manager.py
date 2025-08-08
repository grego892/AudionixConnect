"""
Stream Manager - Core Audio Stream Management

This module handles the creation, management, and monitoring of audio
Senders and Receivers, including RTP multicast stream handling.
"""

import threading
import time
import socket
import struct
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

from .rtp_handler import RTPHandler
from .audio_codec import AudioCodec

logger = logging.getLogger(__name__)

class Sender:
    """Audio Sender class for ingesting and forwarding multicast RTP streams"""
    
    def __init__(self, config: Dict):
        self.id = config['id']
        self.name = config['name']
        self.input_config = config['input']
        self.output_config = config['output']
        self.codec_config = config.get('codec', {'type': 'pcm'})
        
        # Stream state
        self.active = False
        self.input_socket = None
        self.output_socket = None
        self.worker_thread = None
        self.stats = {
            'packets_received': 0,
            'packets_sent': 0,
            'bytes_received': 0,
            'bytes_sent': 0,
            'errors': 0,
            'start_time': None,
            'last_packet_time': None
        }
        
        # Audio processing
        self.rtp_handler = RTPHandler()
        self.audio_codec = AudioCodec(self.codec_config)
        self.audio_levels = {'left': -60.0, 'right': -60.0}
        
    def start(self):
        """Start the sender"""
        try:
            logger.info(f"Starting sender {self.name} ({self.id})")
            
            # Setup input socket for multicast RTP reception
            self._setup_input_socket()
            
            # Setup output socket for forwarding
            self._setup_output_socket()
            
            # Start processing thread
            self.active = True
            self.stats['start_time'] = datetime.now()
            self.worker_thread = threading.Thread(target=self._process_loop)
            self.worker_thread.daemon = True
            self.worker_thread.start()
            
            logger.info(f"Sender {self.name} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start sender {self.name}: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop the sender"""
        logger.info(f"Stopping sender {self.name} ({self.id})")
        
        self.active = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        
        if self.input_socket:
            self.input_socket.close()
            self.input_socket = None
            
        if self.output_socket:
            self.output_socket.close()
            self.output_socket = None
            
        logger.info(f"Sender {self.name} stopped")
    
    def _setup_input_socket(self):
        """Setup multicast input socket"""
        multicast_group = self.input_config['multicast_address']
        port = self.input_config['port']
        interface = self.input_config.get('interface', '0.0.0.0')
        
        # Create socket
        self.input_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.input_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to interface and port
        self.input_socket.bind((interface, port))
        
        # Join multicast group
        mreq = struct.pack("4sl", socket.inet_aton(multicast_group), socket.INADDR_ANY)
        self.input_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        # Set receive buffer size
        self.input_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
        
        logger.info(f"Input socket bound to {multicast_group}:{port}")
    
    def _setup_output_socket(self):
        """Setup output socket for forwarding"""
        self.output_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Set send buffer size
        self.output_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
        
        logger.info("Output socket created for forwarding")
    
    def _process_loop(self):
        """Main processing loop"""
        logger.info(f"Processing loop started for sender {self.name}")
        
        while self.active:
            try:
                # Receive RTP packet
                data, addr = self.input_socket.recvfrom(2048)
                self.stats['packets_received'] += 1
                self.stats['bytes_received'] += len(data)
                self.stats['last_packet_time'] = datetime.now()
                
                # Parse RTP packet
                rtp_packet = self.rtp_handler.parse_packet(data)
                if not rtp_packet:
                    self.stats['errors'] += 1
                    continue
                
                # Extract audio data
                audio_data = rtp_packet['payload']
                
                # Calculate audio levels
                self._calculate_audio_levels(audio_data)
                
                # Process audio (encode if needed)
                processed_audio = self.audio_codec.encode(audio_data)
                
                # Create output packet
                output_packet = self._create_output_packet(processed_audio, rtp_packet)
                
                # Forward to receiver
                self._forward_packet(output_packet)
                
                self.stats['packets_sent'] += 1
                self.stats['bytes_sent'] += len(output_packet)
                
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error in processing loop for {self.name}: {e}")
                self.stats['errors'] += 1
                time.sleep(0.01)  # Brief pause on error
        
        logger.info(f"Processing loop stopped for sender {self.name}")
    
    def _calculate_audio_levels(self, audio_data: bytes):
        """Calculate audio levels for monitoring"""
        try:
            # Convert bytes to 24-bit samples (simplified)
            if len(audio_data) >= 6:  # At least one stereo sample
                # This is a simplified level calculation
                # In production, proper audio level metering would be implemented
                sample_count = len(audio_data) // 6  # 24-bit stereo
                total_left = 0
                total_right = 0
                
                for i in range(0, min(sample_count * 6, len(audio_data)), 6):
                    # Extract 24-bit samples (little-endian)
                    left = int.from_bytes(audio_data[i:i+3], byteorder='little', signed=True)
                    right = int.from_bytes(audio_data[i+3:i+6], byteorder='little', signed=True)
                    
                    total_left += abs(left)
                    total_right += abs(right)
                
                # Calculate RMS and convert to dBFS
                if sample_count > 0:
                    rms_left = (total_left / sample_count) / (2**23)  # Normalize to 24-bit range
                    rms_right = (total_right / sample_count) / (2**23)
                    
                    # Convert to dBFS (with minimum floor)
                    self.audio_levels['left'] = max(-60.0, 20 * math.log10(max(rms_left, 1e-6)))
                    self.audio_levels['right'] = max(-60.0, 20 * math.log10(max(rms_right, 1e-6)))
        except Exception as e:
            logger.debug(f"Error calculating audio levels: {e}")
    
    def _create_output_packet(self, audio_data: bytes, original_rtp: Dict) -> bytes:
        """Create output packet for forwarding"""
        # For now, create a simple packet format
        # In production, this would follow the specified protocol
        header = {
            'sender_id': self.id,
            'timestamp': original_rtp.get('timestamp', 0),
            'sequence': original_rtp.get('sequence', 0),
            'codec': self.codec_config['type'],
            'length': len(audio_data)
        }
        
        header_bytes = json.dumps(header).encode('utf-8')
        header_length = struct.pack('!I', len(header_bytes))
        
        return header_length + header_bytes + audio_data
    
    def _forward_packet(self, packet: bytes):
        """Forward packet to receiver"""
        try:
            dest_address = self.output_config['destination_address']
            dest_port = self.output_config['destination_port']
            
            self.output_socket.sendto(packet, (dest_address, dest_port))
        except Exception as e:
            logger.error(f"Error forwarding packet from {self.name}: {e}")
            self.stats['errors'] += 1
    
    def get_status(self) -> Dict:
        """Get current sender status"""
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'id': self.id,
            'name': self.name,
            'active': self.active,
            'input': self.input_config,
            'output': self.output_config,
            'codec': self.codec_config,
            'stats': self.stats.copy(),
            'uptime': uptime,
            'audio_levels': self.audio_levels.copy()
        }


class Receiver:
    """Audio Receiver class for receiving and outputting multicast RTP streams"""
    
    def __init__(self, config: Dict):
        self.id = config['id']
        self.name = config['name']
        self.input_config = config['input']
        self.output_config = config['output']
        self.codec_config = config.get('codec', {'type': 'pcm'})
        
        # Stream state
        self.active = False
        self.input_socket = None
        self.output_socket = None
        self.worker_thread = None
        self.stats = {
            'packets_received': 0,
            'packets_sent': 0,
            'bytes_received': 0,
            'bytes_sent': 0,
            'errors': 0,
            'start_time': None,
            'last_packet_time': None
        }
        
        # Audio processing
        self.rtp_handler = RTPHandler()
        self.audio_codec = AudioCodec(self.codec_config)
        self.audio_levels = {'left': -60.0, 'right': -60.0}
    
    def start(self):
        """Start the receiver"""
        try:
            logger.info(f"Starting receiver {self.name} ({self.id})")
            
            # Setup input socket for receiving forwarded streams
            self._setup_input_socket()
            
            # Setup output socket for multicast RTP output
            self._setup_output_socket()
            
            # Start processing thread
            self.active = True
            self.stats['start_time'] = datetime.now()
            self.worker_thread = threading.Thread(target=self._process_loop)
            self.worker_thread.daemon = True
            self.worker_thread.start()
            
            logger.info(f"Receiver {self.name} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start receiver {self.name}: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop the receiver"""
        logger.info(f"Stopping receiver {self.name} ({self.id})")
        
        self.active = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        
        if self.input_socket:
            self.input_socket.close()
            self.input_socket = None
            
        if self.output_socket:
            self.output_socket.close()
            self.output_socket = None
            
        logger.info(f"Receiver {self.name} stopped")
    
    def _setup_input_socket(self):
        """Setup input socket for receiving forwarded streams"""
        port = self.input_config['port']
        interface = self.input_config.get('interface', '0.0.0.0')
        
        self.input_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.input_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.input_socket.bind((interface, port))
        
        # Set receive buffer size
        self.input_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
        
        logger.info(f"Input socket bound to {interface}:{port}")
    
    def _setup_output_socket(self):
        """Setup multicast output socket"""
        self.output_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Set TTL for multicast
        ttl = self.output_config.get('ttl', 1)
        self.output_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        
        # Set send buffer size
        self.output_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
        
        logger.info("Output socket created for multicast transmission")
    
    def _process_loop(self):
        """Main processing loop"""
        logger.info(f"Processing loop started for receiver {self.name}")
        
        while self.active:
            try:
                # Receive forwarded packet
                data, addr = self.input_socket.recvfrom(4096)
                self.stats['packets_received'] += 1
                self.stats['bytes_received'] += len(data)
                self.stats['last_packet_time'] = datetime.now()
                
                # Parse forwarded packet
                audio_data = self._parse_input_packet(data)
                if not audio_data:
                    self.stats['errors'] += 1
                    continue
                
                # Calculate audio levels
                self._calculate_audio_levels(audio_data)
                
                # Decode audio if needed
                decoded_audio = self.audio_codec.decode(audio_data)
                
                # Create RTP packet for output
                rtp_packet = self._create_rtp_packet(decoded_audio)
                
                # Send multicast RTP
                self._send_rtp_packet(rtp_packet)
                
                self.stats['packets_sent'] += 1
                self.stats['bytes_sent'] += len(rtp_packet)
                
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error in processing loop for {self.name}: {e}")
                self.stats['errors'] += 1
                time.sleep(0.01)  # Brief pause on error
        
        logger.info(f"Processing loop stopped for receiver {self.name}")
    
    def _parse_input_packet(self, data: bytes) -> Optional[bytes]:
        """Parse input packet to extract audio data"""
        try:
            # Parse header length
            if len(data) < 4:
                return None
            
            header_length = struct.unpack('!I', data[:4])[0]
            if len(data) < 4 + header_length:
                return None
            
            # Parse header
            header_bytes = data[4:4+header_length]
            header = json.loads(header_bytes.decode('utf-8'))
            
            # Extract audio data
            audio_data = data[4+header_length:]
            
            return audio_data
        except Exception as e:
            logger.debug(f"Error parsing input packet: {e}")
            return None
    
    def _calculate_audio_levels(self, audio_data: bytes):
        """Calculate audio levels for monitoring"""
        # Same implementation as Sender
        try:
            if len(audio_data) >= 6:
                sample_count = len(audio_data) // 6
                total_left = 0
                total_right = 0
                
                for i in range(0, min(sample_count * 6, len(audio_data)), 6):
                    left = int.from_bytes(audio_data[i:i+3], byteorder='little', signed=True)
                    right = int.from_bytes(audio_data[i+3:i+6], byteorder='little', signed=True)
                    
                    total_left += abs(left)
                    total_right += abs(right)
                
                if sample_count > 0:
                    rms_left = (total_left / sample_count) / (2**23)
                    rms_right = (total_right / sample_count) / (2**23)
                    
                    import math
                    self.audio_levels['left'] = max(-60.0, 20 * math.log10(max(rms_left, 1e-6)))
                    self.audio_levels['right'] = max(-60.0, 20 * math.log10(max(rms_right, 1e-6)))
        except Exception as e:
            logger.debug(f"Error calculating audio levels: {e}")
    
    def _create_rtp_packet(self, audio_data: bytes) -> bytes:
        """Create RTP packet for multicast output"""
        return self.rtp_handler.create_packet(
            payload_type=self.output_config.get('payload_type', 96),
            timestamp=int(time.time() * 48000) & 0xFFFFFFFF,  # 48kHz timestamp
            ssrc=self.output_config.get('ssrc', hash(self.id) & 0xFFFFFFFF),
            payload=audio_data
        )
    
    def _send_rtp_packet(self, packet: bytes):
        """Send RTP packet to multicast address"""
        try:
            multicast_address = self.output_config['multicast_address']
            port = self.output_config['port']
            
            self.output_socket.sendto(packet, (multicast_address, port))
        except Exception as e:
            logger.error(f"Error sending RTP packet from {self.name}: {e}")
            self.stats['errors'] += 1
    
    def get_status(self) -> Dict:
        """Get current receiver status"""
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'id': self.id,
            'name': self.name,
            'active': self.active,
            'input': self.input_config,
            'output': self.output_config,
            'codec': self.codec_config,
            'stats': self.stats.copy(),
            'uptime': uptime,
            'audio_levels': self.audio_levels.copy()
        }


class StreamManager:
    """Main stream manager for coordinating Senders and Receivers"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.senders: Dict[str, Sender] = {}
        self.receivers: Dict[str, Receiver] = {}
        self.start_time = datetime.now()
        
    def initialize(self):
        """Initialize stream manager with saved configurations"""
        logger.info("Initializing StreamManager")
        
        # Load saved sender configurations
        sender_configs = self.config_manager.get_sender_configs()
        for config in sender_configs:
            self.create_sender(config)
        
        # Load saved receiver configurations
        receiver_configs = self.config_manager.get_receiver_configs()
        for config in receiver_configs:
            self.create_receiver(config)
        
        logger.info(f"StreamManager initialized with {len(self.senders)} senders and {len(self.receivers)} receivers")
    
    def create_sender(self, config: Dict) -> bool:
        """Create a new sender"""
        try:
            sender = Sender(config)
            self.senders[sender.id] = sender
            
            # Save configuration
            self.config_manager.save_sender_config(config)
            
            logger.info(f"Created sender {sender.name} ({sender.id})")
            return True
        except Exception as e:
            logger.error(f"Failed to create sender: {e}")
            return False
    
    def create_receiver(self, config: Dict) -> bool:
        """Create a new receiver"""
        try:
            receiver = Receiver(config)
            self.receivers[receiver.id] = receiver
            
            # Save configuration
            self.config_manager.save_receiver_config(config)
            
            logger.info(f"Created receiver {receiver.name} ({receiver.id})")
            return True
        except Exception as e:
            logger.error(f"Failed to create receiver: {e}")
            return False
    
    def start_sender(self, sender_id: str) -> bool:
        """Start a sender"""
        if sender_id in self.senders:
            return self.senders[sender_id].start()
        return False
    
    def stop_sender(self, sender_id: str) -> bool:
        """Stop a sender"""
        if sender_id in self.senders:
            self.senders[sender_id].stop()
            return True
        return False
    
    def remove_sender(self, sender_id: str) -> bool:
        """Remove a sender"""
        if sender_id in self.senders:
            self.senders[sender_id].stop()
            del self.senders[sender_id]
            self.config_manager.remove_sender_config(sender_id)
            logger.info(f"Removed sender {sender_id}")
            return True
        return False
    
    def start_receiver(self, receiver_id: str) -> bool:
        """Start a receiver"""
        if receiver_id in self.receivers:
            return self.receivers[receiver_id].start()
        return False
    
    def stop_receiver(self, receiver_id: str) -> bool:
        """Stop a receiver"""
        if receiver_id in self.receivers:
            self.receivers[receiver_id].stop()
            return True
        return False
    
    def remove_receiver(self, receiver_id: str) -> bool:
        """Remove a receiver"""
        if receiver_id in self.receivers:
            self.receivers[receiver_id].stop()
            del self.receivers[receiver_id]
            self.config_manager.remove_receiver_config(receiver_id)
            logger.info(f"Removed receiver {receiver_id}")
            return True
        return False
    
    def get_sender_status(self) -> List[Dict]:
        """Get status of all senders"""
        return [sender.get_status() for sender in self.senders.values()]
    
    def get_receiver_status(self) -> List[Dict]:
        """Get status of all receivers"""
        return [receiver.get_status() for receiver in self.receivers.values()]
    
    def get_active_stream_count(self) -> int:
        """Get count of active streams"""
        active_senders = sum(1 for s in self.senders.values() if s.active)
        active_receivers = sum(1 for r in self.receivers.values() if r.active)
        return active_senders + active_receivers
    
    def get_total_bandwidth(self) -> float:
        """Get estimated total bandwidth usage (Mbps)"""
        # Rough calculation: 48kHz * 24-bit * 2 channels = ~2.3 Mbps per stream
        active_streams = self.get_active_stream_count()
        return active_streams * 2.3
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def shutdown(self):
        """Shutdown all senders and receivers"""
        logger.info("Shutting down StreamManager")
        
        for sender in self.senders.values():
            sender.stop()
        
        for receiver in self.receivers.values():
            receiver.stop()
        
        logger.info("StreamManager shutdown complete")
