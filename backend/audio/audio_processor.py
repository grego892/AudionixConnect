"""
Audio Processor - Real-time Audio Level Monitoring

This module provides real-time audio level monitoring and analysis
for active audio streams.
"""

import threading
import time
import math
from collections import deque
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Real-time audio processing and monitoring"""
    
    def __init__(self):
        self.level_data = {}  # Stream ID -> level data
        self.monitoring_active = False
        self.lock = threading.RLock()
        
        # Audio analysis parameters
        self.level_history_size = 100  # Keep 100 samples of level history
        self.peak_hold_time = 1.0      # Hold peaks for 1 second
        self.update_rate = 10          # 10 Hz update rate
        
    def start_monitoring(self):
        """Start audio level monitoring"""
        with self.lock:
            self.monitoring_active = True
        logger.info("Audio processor monitoring started")
    
    def stop_monitoring(self):
        """Stop audio level monitoring"""
        with self.lock:
            self.monitoring_active = False
        logger.info("Audio processor monitoring stopped")
    
    def update_levels(self, stream_id: str, left_level: float, right_level: float):
        """
        Update audio levels for a stream
        
        Args:
            stream_id: Unique identifier for the stream
            left_level: Left channel level in dBFS
            right_level: Right channel level in dBFS
        """
        with self.lock:
            current_time = time.time()
            
            if stream_id not in self.level_data:
                self.level_data[stream_id] = {
                    'left': {
                        'current': -60.0,
                        'peak': -60.0,
                        'peak_time': current_time,
                        'history': deque(maxlen=self.level_history_size)
                    },
                    'right': {
                        'current': -60.0,
                        'peak': -60.0,
                        'peak_time': current_time,
                        'history': deque(maxlen=self.level_history_size)
                    },
                    'last_update': current_time
                }
            
            stream_data = self.level_data[stream_id]
            
            # Update left channel
            stream_data['left']['current'] = left_level
            stream_data['left']['history'].append((current_time, left_level))
            
            if left_level > stream_data['left']['peak']:
                stream_data['left']['peak'] = left_level
                stream_data['left']['peak_time'] = current_time
            elif current_time - stream_data['left']['peak_time'] > self.peak_hold_time:
                # Reset peak if hold time expired
                stream_data['left']['peak'] = left_level
                stream_data['left']['peak_time'] = current_time
            
            # Update right channel
            stream_data['right']['current'] = right_level
            stream_data['right']['history'].append((current_time, right_level))
            
            if right_level > stream_data['right']['peak']:
                stream_data['right']['peak'] = right_level
                stream_data['right']['peak_time'] = current_time
            elif current_time - stream_data['right']['peak_time'] > self.peak_hold_time:
                # Reset peak if hold time expired
                stream_data['right']['peak'] = right_level
                stream_data['right']['peak_time'] = current_time
            
            stream_data['last_update'] = current_time
    
    def get_current_levels(self) -> Dict:
        """
        Get current audio levels for all active streams
        
        Returns:
            Dictionary with stream levels and statistics
        """
        with self.lock:
            if not self.level_data:
                return {}
            
            current_time = time.time()
            result = {}
            
            for stream_id, data in self.level_data.items():
                # Check if stream is still active (recent updates)
                if current_time - data['last_update'] > 5.0:  # 5 second timeout
                    continue
                
                result[stream_id] = {
                    'left': {
                        'current': data['left']['current'],
                        'peak': data['left']['peak'],
                        'rms': self._calculate_rms(data['left']['history']),
                        'clip': data['left']['peak'] > -0.1  # Clipping threshold
                    },
                    'right': {
                        'current': data['right']['current'],
                        'peak': data['right']['peak'],
                        'rms': self._calculate_rms(data['right']['history']),
                        'clip': data['right']['peak'] > -0.1  # Clipping threshold
                    },
                    'stereo': {
                        'correlation': self._calculate_stereo_correlation(data),
                        'balance': self._calculate_balance(data)
                    },
                    'last_update': data['last_update']
                }
            
            return result
    
    def _calculate_rms(self, history: deque) -> float:
        """Calculate RMS level from history"""
        if not history:
            return -60.0
        
        try:
            # Calculate RMS over recent history (last 1 second)
            current_time = time.time()
            recent_samples = [level for timestamp, level in history 
                            if current_time - timestamp <= 1.0]
            
            if not recent_samples:
                return -60.0
            
            # Convert dBFS to linear, calculate RMS, convert back to dBFS
            linear_samples = [10**(level / 20.0) for level in recent_samples]
            rms_linear = math.sqrt(sum(x*x for x in linear_samples) / len(linear_samples))
            rms_db = 20 * math.log10(max(rms_linear, 1e-6))
            
            return max(-60.0, rms_db)
            
        except Exception as e:
            logger.debug(f"Error calculating RMS: {e}")
            return -60.0
    
    def _calculate_stereo_correlation(self, data: Dict) -> float:
        """Calculate stereo correlation coefficient"""
        try:
            left_history = data['left']['history']
            right_history = data['right']['history']
            
            if len(left_history) < 2 or len(right_history) < 2:
                return 0.0
            
            # Get recent samples (last 100 samples or 1 second, whichever is less)
            current_time = time.time()
            left_samples = [level for timestamp, level in left_history 
                          if current_time - timestamp <= 1.0]
            right_samples = [level for timestamp, level in right_history 
                           if current_time - timestamp <= 1.0]
            
            if len(left_samples) != len(right_samples) or len(left_samples) < 2:
                return 0.0
            
            # Convert to linear and calculate correlation
            left_linear = [10**(level / 20.0) for level in left_samples]
            right_linear = [10**(level / 20.0) for level in right_samples]
            
            # Calculate Pearson correlation coefficient
            n = len(left_linear)
            sum_left = sum(left_linear)
            sum_right = sum(right_linear)
            sum_left_sq = sum(x*x for x in left_linear)
            sum_right_sq = sum(x*x for x in right_linear)
            sum_products = sum(left_linear[i] * right_linear[i] for i in range(n))
            
            numerator = n * sum_products - sum_left * sum_right
            denominator = math.sqrt((n * sum_left_sq - sum_left**2) * (n * sum_right_sq - sum_right**2))
            
            if denominator == 0:
                return 0.0
            
            correlation = numerator / denominator
            return max(-1.0, min(1.0, correlation))  # Clamp to [-1, 1]
            
        except Exception as e:
            logger.debug(f"Error calculating stereo correlation: {e}")
            return 0.0
    
    def _calculate_balance(self, data: Dict) -> float:
        """
        Calculate stereo balance (-1.0 = full left, 0.0 = center, 1.0 = full right)
        """
        try:
            left_current = data['left']['current']
            right_current = data['right']['current']
            
            # Convert dBFS to linear
            left_linear = 10**(left_current / 20.0)
            right_linear = 10**(right_current / 20.0)
            
            total_energy = left_linear + right_linear
            if total_energy == 0:
                return 0.0
            
            # Calculate balance
            balance = (right_linear - left_linear) / total_energy
            return max(-1.0, min(1.0, balance))
            
        except Exception as e:
            logger.debug(f"Error calculating balance: {e}")
            return 0.0
    
    def remove_stream(self, stream_id: str):
        """Remove a stream from monitoring"""
        with self.lock:
            if stream_id in self.level_data:
                del self.level_data[stream_id]
                logger.debug(f"Removed stream {stream_id} from audio monitoring")
    
    def clear_all_streams(self):
        """Clear all stream monitoring data"""
        with self.lock:
            self.level_data.clear()
            logger.info("Cleared all audio monitoring data")
    
    def get_stream_statistics(self, stream_id: str) -> Optional[Dict]:
        """Get detailed statistics for a specific stream"""
        with self.lock:
            if stream_id not in self.level_data:
                return None
            
            data = self.level_data[stream_id]
            current_time = time.time()
            
            # Calculate statistics from history
            left_levels = [level for timestamp, level in data['left']['history']
                          if current_time - timestamp <= 10.0]  # Last 10 seconds
            right_levels = [level for timestamp, level in data['right']['history']
                           if current_time - timestamp <= 10.0]
            
            if not left_levels or not right_levels:
                return None
            
            return {
                'stream_id': stream_id,
                'duration': current_time - (data['left']['history'][0][0] if data['left']['history'] else current_time),
                'sample_count': len(left_levels),
                'left': {
                    'current': data['left']['current'],
                    'peak': data['left']['peak'],
                    'rms': self._calculate_rms(data['left']['history']),
                    'min': min(left_levels),
                    'max': max(left_levels),
                    'average': sum(left_levels) / len(left_levels)
                },
                'right': {
                    'current': data['right']['current'],
                    'peak': data['right']['peak'],
                    'rms': self._calculate_rms(data['right']['history']),
                    'min': min(right_levels),
                    'max': max(right_levels),
                    'average': sum(right_levels) / len(right_levels)
                },
                'stereo': {
                    'correlation': self._calculate_stereo_correlation(data),
                    'balance': self._calculate_balance(data)
                }
            }
    
    def detect_silence(self, stream_id: str, threshold_db: float = -40.0, duration_sec: float = 5.0) -> bool:
        """
        Detect if a stream has been silent for a specified duration
        
        Args:
            stream_id: Stream to check
            threshold_db: Silence threshold in dBFS
            duration_sec: Minimum silence duration to detect
            
        Returns:
            True if stream has been silent for the specified duration
        """
        with self.lock:
            if stream_id not in self.level_data:
                return False
            
            data = self.level_data[stream_id]
            current_time = time.time()
            
            # Check recent history for levels above threshold
            for channel in ['left', 'right']:
                for timestamp, level in data[channel]['history']:
                    if current_time - timestamp <= duration_sec and level > threshold_db:
                        return False
            
            return True
    
    def detect_clipping(self, stream_id: str, threshold_db: float = -0.1, duration_sec: float = 1.0) -> bool:
        """
        Detect if a stream has been clipping
        
        Args:
            stream_id: Stream to check
            threshold_db: Clipping threshold in dBFS
            duration_sec: Time window to check
            
        Returns:
            True if clipping detected in the time window
        """
        with self.lock:
            if stream_id not in self.level_data:
                return False
            
            data = self.level_data[stream_id]
            current_time = time.time()
            
            # Check recent history for levels above threshold
            for channel in ['left', 'right']:
                for timestamp, level in data[channel]['history']:
                    if current_time - timestamp <= duration_sec and level > threshold_db:
                        return True
            
            return False
