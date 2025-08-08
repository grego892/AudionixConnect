"""
RTP Handler - Real-time Transport Protocol Implementation

This module handles RTP packet parsing and creation for audio streaming,
supporting both Livewire+ and AES67 formats.
"""

import struct
import random
import time
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class RTPHandler:
    """RTP packet handler for audio streaming"""
    
    def __init__(self):
        self.sequence_number = random.randint(0, 65535)
        self.ssrc = random.randint(0, 2**32 - 1)
        self.timestamp_base = int(time.time() * 48000) & 0xFFFFFFFF
        
    def parse_packet(self, data: bytes) -> Optional[Dict]:
        """
        Parse RTP packet and extract header information and payload
        
        RTP Header Format (RFC 3550):
        0                   1                   2                   3
        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |V=2|P|X|  CC   |M|     PT      |       sequence number         |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                           timestamp                           |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |           synchronization source (SSRC) identifier          |
        +=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
        """
        try:
            if len(data) < 12:  # Minimum RTP header size
                logger.debug("Packet too short for RTP header")
                return None
            
            # Parse fixed header (12 bytes)
            header_data = struct.unpack('!BBHII', data[:12])
            
            vpxcc = header_data[0]
            version = (vpxcc >> 6) & 0x03
            padding = (vpxcc >> 5) & 0x01
            extension = (vpxcc >> 4) & 0x01
            csrc_count = vpxcc & 0x0F
            
            mpt = header_data[1]
            marker = (mpt >> 7) & 0x01
            payload_type = mpt & 0x7F
            
            sequence = header_data[2]
            timestamp = header_data[3]
            ssrc = header_data[4]
            
            # Validate version
            if version != 2:
                logger.debug(f"Invalid RTP version: {version}")
                return None
            
            # Calculate header length
            header_length = 12 + (csrc_count * 4)
            
            # Parse CSRC list if present
            csrc_list = []
            if csrc_count > 0:
                if len(data) < header_length:
                    logger.debug("Packet too short for CSRC list")
                    return None
                
                for i in range(csrc_count):
                    offset = 12 + (i * 4)
                    csrc = struct.unpack('!I', data[offset:offset+4])[0]
                    csrc_list.append(csrc)
            
            # Handle extension header if present
            extension_data = None
            if extension:
                if len(data) < header_length + 4:
                    logger.debug("Packet too short for extension header")
                    return None
                
                ext_header = struct.unpack('!HH', data[header_length:header_length+4])
                ext_length = ext_header[1] * 4  # Length in 32-bit words
                
                if len(data) < header_length + 4 + ext_length:
                    logger.debug("Packet too short for extension data")
                    return None
                
                extension_data = {
                    'profile': ext_header[0],
                    'length': ext_length,
                    'data': data[header_length+4:header_length+4+ext_length]
                }
                header_length += 4 + ext_length
            
            # Extract payload
            payload_start = header_length
            payload_end = len(data)
            
            # Handle padding if present
            if padding:
                if len(data) > payload_start:
                    padding_length = data[-1]
                    payload_end -= padding_length
                else:
                    logger.debug("Invalid padding")
                    return None
            
            payload = data[payload_start:payload_end]
            
            return {
                'version': version,
                'padding': bool(padding),
                'extension': bool(extension),
                'marker': bool(marker),
                'payload_type': payload_type,
                'sequence': sequence,
                'timestamp': timestamp,
                'ssrc': ssrc,
                'csrc_list': csrc_list,
                'extension_data': extension_data,
                'payload': payload,
                'header_length': header_length,
                'payload_length': len(payload)
            }
            
        except Exception as e:
            logger.error(f"Error parsing RTP packet: {e}")
            return None
    
    def create_packet(self, payload_type: int, timestamp: int, ssrc: int, payload: bytes, 
                     marker: bool = False, extension_data: Optional[bytes] = None) -> bytes:
        """
        Create RTP packet with given parameters
        """
        try:
            # Increment sequence number
            self.sequence_number = (self.sequence_number + 1) % 65536
            
            # Build fixed header
            version = 2
            padding = 0
            extension = 1 if extension_data else 0
            csrc_count = 0
            
            vpxcc = (version << 6) | (padding << 5) | (extension << 4) | csrc_count
            mpt = (int(marker) << 7) | (payload_type & 0x7F)
            
            header = struct.pack('!BBHII', 
                               vpxcc, mpt, self.sequence_number, 
                               timestamp, ssrc)
            
            packet = header
            
            # Add extension header if present
            if extension_data:
                # Simple extension format
                ext_length = (len(extension_data) + 3) // 4  # Round up to 32-bit words
                padded_ext_data = extension_data + b'\x00' * (ext_length * 4 - len(extension_data))
                
                ext_header = struct.pack('!HH', 0x0000, ext_length)  # Profile-specific extension
                packet += ext_header + padded_ext_data
            
            # Add payload
            packet += payload
            
            return packet
            
        except Exception as e:
            logger.error(f"Error creating RTP packet: {e}")
            return b''
    
    def validate_livewire_plus(self, rtp_packet: Dict) -> bool:
        """
        Validate RTP packet for Livewire+ compliance
        
        Livewire+ specifications:
        - Payload Type: Dynamic (typically 96-127)
        - Sample Rate: 48 kHz
        - Bit Depth: 24-bit
        - Channels: Up to 8 (typically stereo)
        - Packet size: Typically 240 samples (5ms at 48kHz)
        """
        try:
            # Check payload type range
            if not (96 <= rtp_packet['payload_type'] <= 127):
                logger.debug(f"Non-dynamic payload type for Livewire+: {rtp_packet['payload_type']}")
            
            # Check payload size for typical Livewire+ packet
            # 240 samples * 2 channels * 3 bytes = 1440 bytes
            payload_length = rtp_packet['payload_length']
            
            # Common Livewire+ packet sizes (in bytes)
            valid_sizes = [1440, 720, 360, 180]  # 5ms, 2.5ms, 1.25ms, 0.625ms at 48kHz stereo 24-bit
            
            if payload_length not in valid_sizes:
                logger.debug(f"Unusual payload size for Livewire+: {payload_length} bytes")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating Livewire+ packet: {e}")
            return False
    
    def validate_aes67(self, rtp_packet: Dict) -> bool:
        """
        Validate RTP packet for AES67 compliance
        
        AES67 specifications:
        - Payload Type: Dynamic (96-127) or Static (L16: 10-11)
        - Sample Rate: 48 kHz (primary), 44.1 kHz, 96 kHz supported
        - Bit Depth: 16-bit (L16), 24-bit supported
        - Packet time: 1ms typical, up to 4ms
        """
        try:
            payload_type = rtp_packet['payload_type']
            
            # Check payload type
            if not ((10 <= payload_type <= 11) or (96 <= payload_type <= 127)):
                logger.debug(f"Invalid payload type for AES67: {payload_type}")
            
            # Check payload size for common AES67 configurations
            payload_length = rtp_packet['payload_length']
            
            # Common AES67 packet sizes:
            # 1ms at 48kHz: 48 samples * 2 channels * 3 bytes = 288 bytes (24-bit)
            # 1ms at 48kHz: 48 samples * 2 channels * 2 bytes = 192 bytes (16-bit)
            valid_sizes_24bit = [288, 576, 864, 1152]  # 1ms, 2ms, 3ms, 4ms
            valid_sizes_16bit = [192, 384, 576, 768]   # 1ms, 2ms, 3ms, 4ms
            
            if payload_length not in (valid_sizes_24bit + valid_sizes_16bit):
                logger.debug(f"Unusual payload size for AES67: {payload_length} bytes")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating AES67 packet: {e}")
            return False
    
    def extract_audio_samples(self, rtp_packet: Dict, bit_depth: int = 24, channels: int = 2) -> Optional[Tuple[int, bytes]]:
        """
        Extract audio samples from RTP payload
        
        Returns:
            Tuple of (sample_count, audio_data) or None if invalid
        """
        try:
            payload = rtp_packet['payload']
            bytes_per_sample = bit_depth // 8
            bytes_per_frame = bytes_per_sample * channels
            
            if len(payload) % bytes_per_frame != 0:
                logger.debug(f"Payload length {len(payload)} not aligned to frame size {bytes_per_frame}")
                # Truncate to frame boundary
                aligned_length = (len(payload) // bytes_per_frame) * bytes_per_frame
                payload = payload[:aligned_length]
            
            sample_count = len(payload) // bytes_per_frame
            
            return sample_count, payload
            
        except Exception as e:
            logger.error(f"Error extracting audio samples: {e}")
            return None
    
    def create_audio_payload(self, audio_data: bytes, bit_depth: int = 24, channels: int = 2) -> bytes:
        """
        Create RTP payload from audio data
        
        Ensures proper alignment and formatting for audio transmission
        """
        try:
            bytes_per_sample = bit_depth // 8
            bytes_per_frame = bytes_per_sample * channels
            
            # Ensure data is frame-aligned
            if len(audio_data) % bytes_per_frame != 0:
                # Pad with zeros to frame boundary
                padding_needed = bytes_per_frame - (len(audio_data) % bytes_per_frame)
                audio_data += b'\x00' * padding_needed
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error creating audio payload: {e}")
            return b''
    
    def calculate_timestamp_increment(self, sample_rate: int, packet_samples: int) -> int:
        """
        Calculate RTP timestamp increment for next packet
        """
        return packet_samples
    
    def detect_stream_format(self, rtp_packet: Dict) -> Dict:
        """
        Attempt to detect stream format from RTP packet characteristics
        """
        try:
            payload_length = rtp_packet['payload_length']
            payload_type = rtp_packet['payload_type']
            
            format_info = {
                'protocol': 'unknown',
                'sample_rate': 48000,  # Default assumption
                'bit_depth': 24,       # Default assumption
                'channels': 2,         # Default assumption
                'packet_time_ms': 0
            }
            
            # Analyze payload type
            if 10 <= payload_type <= 11:
                format_info['protocol'] = 'AES67-L16'
                format_info['bit_depth'] = 16
            elif 96 <= payload_type <= 127:
                format_info['protocol'] = 'AES67-Dynamic'
                
                # Try to detect bit depth from payload size
                if payload_length in [192, 384, 576, 768]:
                    format_info['bit_depth'] = 16
                elif payload_length in [288, 576, 864, 1152]:
                    format_info['bit_depth'] = 24
                elif payload_length in [1440, 720, 360, 180]:
                    format_info['protocol'] = 'Livewire+'
                    format_info['bit_depth'] = 24
            
            # Calculate packet time
            bytes_per_sample = format_info['bit_depth'] // 8
            bytes_per_frame = bytes_per_sample * format_info['channels']
            
            if bytes_per_frame > 0:
                samples_per_packet = payload_length // bytes_per_frame
                format_info['packet_time_ms'] = (samples_per_packet * 1000) // format_info['sample_rate']
            
            return format_info
            
        except Exception as e:
            logger.error(f"Error detecting stream format: {e}")
            return {'protocol': 'unknown', 'sample_rate': 48000, 'bit_depth': 24, 'channels': 2, 'packet_time_ms': 0}
