"""
Audio Codec - Audio Encoding and Decoding

This module provides audio encoding and decoding functionality,
supporting both uncompressed PCM and Opus encoding for efficient transmission.
"""

import struct
import logging
from typing import Optional, Dict, Any
import io

logger = logging.getLogger(__name__)

try:
    import opuslib
    OPUS_AVAILABLE = True
except ImportError:
    OPUS_AVAILABLE = False
    logger.warning("Opus codec not available. Install python-opuslib for Opus support.")

class AudioCodec:
    """Audio codec handler supporting PCM and Opus formats"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.codec_type = config.get('type', 'pcm').lower()
        
        # Audio parameters
        self.sample_rate = config.get('sample_rate', 48000)
        self.channels = config.get('channels', 2)
        self.bit_depth = config.get('bit_depth', 24)
        
        # Opus-specific parameters
        self.opus_bitrate = config.get('opus_bitrate', 128000)  # 128 kbps default
        self.opus_frame_size = config.get('opus_frame_size', 480)  # 10ms at 48kHz
        self.opus_complexity = config.get('opus_complexity', 10)  # Max quality
        
        # Initialize codec
        self.opus_encoder = None
        self.opus_decoder = None
        
        if self.codec_type == 'opus':
            self._initialize_opus()
    
    def _initialize_opus(self):
        """Initialize Opus encoder and decoder"""
        if not OPUS_AVAILABLE:
            logger.error("Cannot initialize Opus codec - opuslib not available")
            raise RuntimeError("Opus codec not available")
        
        try:
            # Create Opus encoder
            self.opus_encoder = opuslib.Encoder(
                fs=self.sample_rate,
                channels=self.channels,
                application=opuslib.APPLICATION_AUDIO
            )
            
            # Set encoder parameters
            self.opus_encoder.bitrate = self.opus_bitrate
            self.opus_encoder.complexity = self.opus_complexity
            self.opus_encoder.signal = opuslib.SIGNAL_MUSIC
            
            # Create Opus decoder
            self.opus_decoder = opuslib.Decoder(
                fs=self.sample_rate,
                channels=self.channels
            )
            
            logger.info(f"Opus codec initialized: {self.sample_rate}Hz, {self.channels}ch, {self.opus_bitrate}bps")
            
        except Exception as e:
            logger.error(f"Failed to initialize Opus codec: {e}")
            raise
    
    def encode(self, audio_data: bytes) -> bytes:
        """
        Encode audio data according to configured codec
        
        Args:
            audio_data: Raw audio data (PCM)
            
        Returns:
            Encoded audio data
        """
        try:
            if self.codec_type == 'pcm':
                return self._encode_pcm(audio_data)
            elif self.codec_type == 'opus':
                return self._encode_opus(audio_data)
            else:
                logger.error(f"Unsupported codec type: {self.codec_type}")
                return audio_data
                
        except Exception as e:
            logger.error(f"Error encoding audio: {e}")
            return audio_data
    
    def decode(self, encoded_data: bytes) -> bytes:
        """
        Decode audio data according to configured codec
        
        Args:
            encoded_data: Encoded audio data
            
        Returns:
            Decoded PCM audio data
        """
        try:
            if self.codec_type == 'pcm':
                return self._decode_pcm(encoded_data)
            elif self.codec_type == 'opus':
                return self._decode_opus(encoded_data)
            else:
                logger.error(f"Unsupported codec type: {self.codec_type}")
                return encoded_data
                
        except Exception as e:
            logger.error(f"Error decoding audio: {e}")
            return encoded_data
    
    def _encode_pcm(self, audio_data: bytes) -> bytes:
        """
        PCM encoding (pass-through with optional format conversion)
        """
        # For PCM, we primarily handle format validation and conversion
        
        # Validate input data length
        bytes_per_sample = self.bit_depth // 8
        bytes_per_frame = bytes_per_sample * self.channels
        
        if len(audio_data) % bytes_per_frame != 0:
            logger.warning(f"Audio data length {len(audio_data)} not aligned to frame size {bytes_per_frame}")
            # Truncate to frame boundary
            aligned_length = (len(audio_data) // bytes_per_frame) * bytes_per_frame
            audio_data = audio_data[:aligned_length]
        
        # Create PCM header for transmission
        header = self._create_pcm_header(len(audio_data))
        
        return header + audio_data
    
    def _decode_pcm(self, encoded_data: bytes) -> bytes:
        """
        PCM decoding (extract audio data from encoded format)
        """
        try:
            # Parse PCM header
            if len(encoded_data) < 16:  # Minimum header size
                logger.error("PCM data too short for header")
                return encoded_data
            
            header = self._parse_pcm_header(encoded_data[:16])
            if not header:
                logger.error("Invalid PCM header")
                return encoded_data
            
            # Extract audio data
            audio_data = encoded_data[16:16 + header['data_length']]
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error decoding PCM: {e}")
            return encoded_data
    
    def _create_pcm_header(self, data_length: int) -> bytes:
        """
        Create PCM header for transmission
        
        Header format (16 bytes):
        - Magic: 4 bytes ('APCM')
        - Sample Rate: 4 bytes (little-endian)
        - Channels: 2 bytes (little-endian)
        - Bit Depth: 2 bytes (little-endian)
        - Data Length: 4 bytes (little-endian)
        """
        try:
            header = struct.pack('<4sIHHI',
                               b'APCM',
                               self.sample_rate,
                               self.channels,
                               self.bit_depth,
                               data_length)
            return header
            
        except Exception as e:
            logger.error(f"Error creating PCM header: {e}")
            return b'\x00' * 16
    
    def _parse_pcm_header(self, header_data: bytes) -> Optional[Dict]:
        """Parse PCM header and return parameters"""
        try:
            if len(header_data) < 16:
                return None
            
            magic, sample_rate, channels, bit_depth, data_length = struct.unpack('<4sIHHI', header_data)
            
            if magic != b'APCM':
                logger.debug(f"Invalid PCM magic: {magic}")
                return None
            
            return {
                'sample_rate': sample_rate,
                'channels': channels,
                'bit_depth': bit_depth,
                'data_length': data_length
            }
            
        except Exception as e:
            logger.error(f"Error parsing PCM header: {e}")
            return None
    
    def _encode_opus(self, audio_data: bytes) -> bytes:
        """
        Opus encoding
        """
        if not self.opus_encoder:
            logger.error("Opus encoder not initialized")
            return audio_data
        
        try:
            # Convert 24-bit to 16-bit for Opus (which expects 16-bit input)
            pcm_16bit = self._convert_24bit_to_16bit(audio_data)
            
            # Encode frames
            encoded_frames = []
            frame_size = self.opus_frame_size * self.channels * 2  # 16-bit samples
            
            for i in range(0, len(pcm_16bit), frame_size):
                frame = pcm_16bit[i:i + frame_size]
                
                # Pad frame if necessary
                if len(frame) < frame_size:
                    frame += b'\x00' * (frame_size - len(frame))
                
                # Encode frame
                encoded_frame = self.opus_encoder.encode(frame, self.opus_frame_size)
                encoded_frames.append(encoded_frame)
            
            # Create Opus packet format
            return self._create_opus_packet(encoded_frames)
            
        except Exception as e:
            logger.error(f"Error encoding Opus: {e}")
            return audio_data
    
    def _decode_opus(self, encoded_data: bytes) -> bytes:
        """
        Opus decoding
        """
        if not self.opus_decoder:
            logger.error("Opus decoder not initialized")
            return encoded_data
        
        try:
            # Parse Opus packet
            frames = self._parse_opus_packet(encoded_data)
            if not frames:
                return encoded_data
            
            # Decode frames
            decoded_frames = []
            for frame in frames:
                decoded_frame = self.opus_decoder.decode(frame, self.opus_frame_size)
                decoded_frames.append(decoded_frame)
            
            # Combine frames
            pcm_16bit = b''.join(decoded_frames)
            
            # Convert back to 24-bit
            pcm_24bit = self._convert_16bit_to_24bit(pcm_16bit)
            
            return pcm_24bit
            
        except Exception as e:
            logger.error(f"Error decoding Opus: {e}")
            return encoded_data
    
    def _create_opus_packet(self, encoded_frames: list) -> bytes:
        """
        Create Opus packet format for transmission
        
        Packet format:
        - Magic: 4 bytes ('OPUS')
        - Frame Count: 4 bytes
        - Frame Sizes: 4 bytes per frame
        - Frames: Variable length
        """
        try:
            packet = struct.pack('<4sI', b'OPUS', len(encoded_frames))
            
            # Add frame sizes
            for frame in encoded_frames:
                packet += struct.pack('<I', len(frame))
            
            # Add frame data
            for frame in encoded_frames:
                packet += frame
            
            return packet
            
        except Exception as e:
            logger.error(f"Error creating Opus packet: {e}")
            return b''
    
    def _parse_opus_packet(self, packet_data: bytes) -> Optional[list]:
        """Parse Opus packet and return frames"""
        try:
            if len(packet_data) < 8:
                return None
            
            magic, frame_count = struct.unpack('<4sI', packet_data[:8])
            
            if magic != b'OPUS':
                logger.debug(f"Invalid Opus magic: {magic}")
                return None
            
            # Read frame sizes
            frame_sizes = []
            offset = 8
            for i in range(frame_count):
                if offset + 4 > len(packet_data):
                    return None
                frame_size = struct.unpack('<I', packet_data[offset:offset+4])[0]
                frame_sizes.append(frame_size)
                offset += 4
            
            # Read frames
            frames = []
            for frame_size in frame_sizes:
                if offset + frame_size > len(packet_data):
                    return None
                frame = packet_data[offset:offset + frame_size]
                frames.append(frame)
                offset += frame_size
            
            return frames
            
        except Exception as e:
            logger.error(f"Error parsing Opus packet: {e}")
            return None
    
    def _convert_24bit_to_16bit(self, audio_24bit: bytes) -> bytes:
        """Convert 24-bit audio to 16-bit for Opus processing"""
        try:
            if len(audio_24bit) % 3 != 0:
                # Align to 24-bit sample boundary
                audio_24bit = audio_24bit[:len(audio_24bit) - (len(audio_24bit) % 3)]
            
            samples_16bit = []
            
            for i in range(0, len(audio_24bit), 3):
                # Read 24-bit sample (little-endian)
                sample_24 = int.from_bytes(audio_24bit[i:i+3], byteorder='little', signed=True)
                
                # Convert to 16-bit (shift right by 8 bits)
                sample_16 = sample_24 >> 8
                
                # Clamp to 16-bit range
                sample_16 = max(-32768, min(32767, sample_16))
                
                samples_16bit.append(struct.pack('<h', sample_16))
            
            return b''.join(samples_16bit)
            
        except Exception as e:
            logger.error(f"Error converting 24-bit to 16-bit: {e}")
            return b''
    
    def _convert_16bit_to_24bit(self, audio_16bit: bytes) -> bytes:
        """Convert 16-bit audio back to 24-bit"""
        try:
            if len(audio_16bit) % 2 != 0:
                # Align to 16-bit sample boundary
                audio_16bit = audio_16bit[:len(audio_16bit) - 1]
            
            samples_24bit = []
            
            for i in range(0, len(audio_16bit), 2):
                # Read 16-bit sample (little-endian)
                sample_16 = struct.unpack('<h', audio_16bit[i:i+2])[0]
                
                # Convert to 24-bit (shift left by 8 bits)
                sample_24 = sample_16 << 8
                
                # Pack as 24-bit (little-endian)
                sample_bytes = sample_24.to_bytes(3, byteorder='little', signed=True)
                samples_24bit.append(sample_bytes)
            
            return b''.join(samples_24bit)
            
        except Exception as e:
            logger.error(f"Error converting 16-bit to 24-bit: {e}")
            return b''
    
    def get_codec_info(self) -> Dict[str, Any]:
        """Get codec configuration information"""
        info = {
            'type': self.codec_type,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'bit_depth': self.bit_depth
        }
        
        if self.codec_type == 'opus':
            info.update({
                'opus_bitrate': self.opus_bitrate,
                'opus_frame_size': self.opus_frame_size,
                'opus_complexity': self.opus_complexity,
                'opus_available': OPUS_AVAILABLE
            })
        
        return info
    
    def estimate_bitrate(self, audio_data_length: int, duration_ms: int) -> float:
        """
        Estimate bitrate for given audio data
        
        Returns bitrate in kbps
        """
        if duration_ms <= 0:
            return 0.0
        
        bits = audio_data_length * 8
        bitrate_bps = (bits * 1000) / duration_ms
        return bitrate_bps / 1000.0  # Convert to kbps
    
    def calculate_frame_size(self, duration_ms: float) -> int:
        """Calculate frame size in samples for given duration"""
        return int((self.sample_rate * duration_ms) / 1000.0)
    
    def validate_audio_format(self, audio_data: bytes) -> bool:
        """Validate audio data format compatibility"""
        try:
            bytes_per_sample = self.bit_depth // 8
            bytes_per_frame = bytes_per_sample * self.channels
            
            # Check alignment
            if len(audio_data) % bytes_per_frame != 0:
                logger.warning(f"Audio data not aligned to frame size ({bytes_per_frame} bytes)")
                return False
            
            # Check minimum size
            if len(audio_data) < bytes_per_frame:
                logger.warning("Audio data too short")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating audio format: {e}")
            return False
