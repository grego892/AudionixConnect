"""
Audio processing module for AudionixConnect.
"""

import numpy as np
import logging
from typing import Optional, Tuple, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SAMPLE_RATE = 48000  # 48kHz for AES67/Livewire
BITS_PER_SAMPLE = 24
CHANNELS = 2  # Stereo


class AudioProcessor:
    """Base class for audio processing."""
    
    def __init__(self):
        """Initialize the audio processor."""
        self.sample_rate = SAMPLE_RATE
        self.bits_per_sample = BITS_PER_SAMPLE
        self.channels = CHANNELS
    
    def process_packet(self, payload: bytes) -> np.ndarray:
        """
        Process audio payload from an RTP packet.
        
        Args:
            payload: Raw audio payload data
            
        Returns:
            NumPy array of audio samples
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def prepare_payload(self, audio_data: np.ndarray) -> bytes:
        """
        Prepare audio data for transmission.
        
        Args:
            audio_data: NumPy array of audio samples
            
        Returns:
            Bytes payload ready for transmission
        """
        raise NotImplementedError("Subclasses must implement this method")


class PCMProcessor(AudioProcessor):
    """Processor for uncompressed PCM audio."""
    
    def __init__(self):
        """Initialize PCM processor."""
        super().__init__()
        self.bytes_per_sample = self.bits_per_sample // 8
        if self.bits_per_sample % 8 != 0:
            self.bytes_per_sample += 1  # Round up for non-multiple of 8
    
    def process_packet(self, payload: bytes) -> np.ndarray:
        """
        Process PCM audio payload.
        
        Args:
            payload: Raw PCM audio data
            
        Returns:
            NumPy array of audio samples
        """
        try:
            # Calculate number of samples in the payload
            bytes_per_frame = self.bytes_per_sample * self.channels
            num_frames = len(payload) // bytes_per_frame
            
            # Reshape into samples
            samples = []
            
            for i in range(num_frames):
                frame = []
                for c in range(self.channels):
                    offset = i * bytes_per_frame + c * self.bytes_per_sample
                    if offset + self.bytes_per_sample <= len(payload):
                        # Extract the bytes for this sample
                        sample_bytes = payload[offset:offset + self.bytes_per_sample]
                        
                        # Convert to integer (24-bit PCM is typically stored in 3 bytes)
                        if self.bytes_per_sample == 3:  # 24-bit audio
                            # Extend to 4 bytes for easier conversion to int32
                            sample_bytes = sample_bytes + b'\x00'
                            sample_val = int.from_bytes(sample_bytes, byteorder='little', signed=True)
                            # Scale to float between -1.0 and 1.0
                            sample = sample_val / (2**(8*self.bytes_per_sample-1))
                        else:  # For other bit depths
                            sample_val = int.from_bytes(sample_bytes, byteorder='little', signed=True)
                            sample = sample_val / (2**(8*self.bytes_per_sample-1))
                            
                        frame.append(sample)
                
                if len(frame) == self.channels:
                    samples.append(frame)
            
            return np.array(samples, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error processing PCM packet: {e}")
            return np.array([], dtype=np.float32)
    
    def prepare_payload(self, audio_data: np.ndarray) -> bytes:
        """
        Convert audio data to PCM bytes.
        
        Args:
            audio_data: NumPy array of audio samples
            
        Returns:
            Bytes payload of PCM data
        """
        try:
            # Ensure audio_data is float32 between -1.0 and 1.0
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Scale to the appropriate range for the bit depth
            scaled = audio_data * (2**(self.bits_per_sample-1) - 1)
            
            # Convert to integers
            ints = scaled.astype(np.int32)
            
            # Convert to bytes
            result = bytearray()
            for frame in ints:
                for sample in frame:
                    # Convert to bytes, keep only the bytes_per_sample bytes
                    sample_bytes = sample.tobytes()[:self.bytes_per_sample]
                    result.extend(sample_bytes)
            
            return bytes(result)
        except Exception as e:
            logger.error(f"Error preparing PCM payload: {e}")
            return b''


class OpusProcessor(AudioProcessor):
    """Processor for Opus-encoded audio."""
    
    def __init__(self, bitrate: int = 128000):
        """
        Initialize Opus processor.
        
        Args:
            bitrate: Target bitrate in bits per second
        """
        super().__init__()
        self.bitrate = bitrate
        
        try:
            import opuslib
            self.encoder = opuslib.Encoder(
                fs=self.sample_rate,
                channels=self.channels,
                application=opuslib.APPLICATION_AUDIO
            )
            self.encoder.bitrate = self.bitrate
            
            self.decoder = opuslib.Decoder(
                fs=self.sample_rate,
                channels=self.channels
            )
            
            self.frame_size = 960  # 20ms at 48kHz
            self.pcm_processor = PCMProcessor()  # For converting between PCM and numpy arrays
            self.has_opus = True
            
        except ImportError:
            logger.error("Failed to import opuslib. Opus encoding/decoding will not work.")
            self.has_opus = False
    
    def process_packet(self, payload: bytes) -> np.ndarray:
        """
        Process Opus-encoded audio payload.
        
        Args:
            payload: Raw Opus-encoded audio data
            
        Returns:
            NumPy array of audio samples
        """
        if not self.has_opus:
            logger.error("Opus processing not available")
            return np.array([], dtype=np.float32)
        
        try:
            # Decode Opus packet
            pcm_data = self.decoder.decode(payload, self.frame_size)
            
            # Convert PCM data to numpy array
            return self.pcm_processor.process_packet(pcm_data)
        except Exception as e:
            logger.error(f"Error processing Opus packet: {e}")
            return np.array([], dtype=np.float32)
    
    def prepare_payload(self, audio_data: np.ndarray) -> bytes:
        """
        Encode audio data using Opus.
        
        Args:
            audio_data: NumPy array of audio samples
            
        Returns:
            Bytes payload of Opus-encoded data
        """
        if not self.has_opus:
            logger.error("Opus processing not available")
            return b''
        
        try:
            # Convert numpy array to PCM
            pcm_data = self.pcm_processor.prepare_payload(audio_data)
            
            # Encode with Opus
            opus_data = self.encoder.encode(pcm_data, self.frame_size)
            
            return opus_data
        except Exception as e:
            logger.error(f"Error preparing Opus payload: {e}")
            return b''


def create_processor(encoding: str, bitrate: Optional[int] = None) -> AudioProcessor:
    """
    Factory function to create the appropriate audio processor.
    
    Args:
        encoding: Audio encoding type (pcm or opus)
        bitrate: Bitrate for Opus encoding (ignored for PCM)
        
    Returns:
        An AudioProcessor instance for the specified encoding
        
    Raises:
        ValueError: If an unsupported encoding is specified
    """
    if encoding.lower() == "pcm":
        return PCMProcessor()
    elif encoding.lower() == "opus":
        if bitrate is None:
            bitrate = 128000  # Default bitrate
        return OpusProcessor(bitrate)
    else:
        raise ValueError(f"Unsupported encoding: {encoding}")
