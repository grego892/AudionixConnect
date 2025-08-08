"""
Configuration Manager - JSON Configuration Storage and Management

This module handles loading, saving, and managing all system configurations
stored in JSON format.
"""

import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Configuration management for AudionixConnect system"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = config_dir
        self.system_config_file = os.path.join(config_dir, "system.json")
        self.senders_config_file = os.path.join(config_dir, "senders.json")
        self.receivers_config_file = os.path.join(config_dir, "receivers.json")
        
        # Configuration data
        self.system_config = {}
        self.sender_configs = {}
        self.receiver_configs = {}
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Ensure config directory exists
        self._ensure_config_directory()
        
        # Load default configurations
        self._load_default_configs()
    
    def _ensure_config_directory(self):
        """Ensure configuration directory exists"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            logger.info(f"Configuration directory: {os.path.abspath(self.config_dir)}")
        except Exception as e:
            logger.error(f"Failed to create config directory: {e}")
            raise
    
    def _load_default_configs(self):
        """Load default system configuration"""
        self.system_config = {
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "audio": {
                "default_sample_rate": 48000,
                "default_bit_depth": 24,
                "default_channels": 2,
                "supported_codecs": ["pcm", "opus"],
                "level_update_rate": 10,
                "peak_hold_time": 1.0
            },
            "network": {
                "default_ttl": 1,
                "receive_buffer_size": 1048576,
                "send_buffer_size": 1048576,
                "multicast_interface": "0.0.0.0"
            },
            "monitoring": {
                "status_update_rate": 10,
                "stream_timeout": 5.0,
                "silence_threshold": -40.0,
                "clipping_threshold": -0.1
            },
            "system": {
                "max_senders": 32,
                "max_receivers": 32,
                "log_level": "INFO"
            }
        }
    
    def load_config(self):
        """Load all configurations from disk"""
        with self.lock:
            try:
                # Load system configuration
                if os.path.exists(self.system_config_file):
                    with open(self.system_config_file, 'r') as f:
                        loaded_config = json.load(f)
                        # Merge with defaults
                        self._merge_config(self.system_config, loaded_config)
                    logger.info("Loaded system configuration")
                else:
                    # Save default configuration
                    self.save_system_config()
                    logger.info("Created default system configuration")
                
                # Load sender configurations
                if os.path.exists(self.senders_config_file):
                    with open(self.senders_config_file, 'r') as f:
                        self.sender_configs = json.load(f)
                    logger.info(f"Loaded {len(self.sender_configs)} sender configurations")
                
                # Load receiver configurations
                if os.path.exists(self.receivers_config_file):
                    with open(self.receivers_config_file, 'r') as f:
                        self.receiver_configs = json.load(f)
                    logger.info(f"Loaded {len(self.receiver_configs)} receiver configurations")
                
            except Exception as e:
                logger.error(f"Error loading configurations: {e}")
                raise
    
    def _merge_config(self, default: Dict, loaded: Dict):
        """Recursively merge loaded config with defaults"""
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value
    
    def save_system_config(self):
        """Save system configuration to disk"""
        with self.lock:
            try:
                self.system_config["last_modified"] = datetime.now().isoformat()
                
                with open(self.system_config_file, 'w') as f:
                    json.dump(self.system_config, f, indent=4)
                logger.debug("Saved system configuration")
                
            except Exception as e:
                logger.error(f"Error saving system configuration: {e}")
                raise
    
    def get_system_config(self) -> Dict:
        """Get current system configuration"""
        with self.lock:
            return self.system_config.copy()
    
    def update_system_config(self, new_config: Dict):
        """Update system configuration"""
        with self.lock:
            try:
                # Merge new configuration
                self._merge_config(self.system_config, new_config)
                
                # Save to disk
                self.save_system_config()
                
                logger.info("Updated system configuration")
                
            except Exception as e:
                logger.error(f"Error updating system configuration: {e}")
                raise
    
    def save_sender_config(self, sender_config: Dict):
        """Save sender configuration"""
        with self.lock:
            try:
                sender_id = sender_config['id']
                sender_config['last_modified'] = datetime.now().isoformat()
                
                self.sender_configs[sender_id] = sender_config
                
                with open(self.senders_config_file, 'w') as f:
                    json.dump(self.sender_configs, f, indent=4)
                
                logger.debug(f"Saved sender configuration: {sender_id}")
                
            except Exception as e:
                logger.error(f"Error saving sender configuration: {e}")
                raise
    
    def remove_sender_config(self, sender_id: str):
        """Remove sender configuration"""
        with self.lock:
            try:
                if sender_id in self.sender_configs:
                    del self.sender_configs[sender_id]
                    
                    with open(self.senders_config_file, 'w') as f:
                        json.dump(self.sender_configs, f, indent=4)
                    
                    logger.debug(f"Removed sender configuration: {sender_id}")
                
            except Exception as e:
                logger.error(f"Error removing sender configuration: {e}")
                raise
    
    def get_sender_configs(self) -> List[Dict]:
        """Get all sender configurations"""
        with self.lock:
            return list(self.sender_configs.values())
    
    def get_sender_config(self, sender_id: str) -> Optional[Dict]:
        """Get specific sender configuration"""
        with self.lock:
            return self.sender_configs.get(sender_id)
    
    def save_receiver_config(self, receiver_config: Dict):
        """Save receiver configuration"""
        with self.lock:
            try:
                receiver_id = receiver_config['id']
                receiver_config['last_modified'] = datetime.now().isoformat()
                
                self.receiver_configs[receiver_id] = receiver_config
                
                with open(self.receivers_config_file, 'w') as f:
                    json.dump(self.receiver_configs, f, indent=4)
                
                logger.debug(f"Saved receiver configuration: {receiver_id}")
                
            except Exception as e:
                logger.error(f"Error saving receiver configuration: {e}")
                raise
    
    def remove_receiver_config(self, receiver_id: str):
        """Remove receiver configuration"""
        with self.lock:
            try:
                if receiver_id in self.receiver_configs:
                    del self.receiver_configs[receiver_id]
                    
                    with open(self.receivers_config_file, 'w') as f:
                        json.dump(self.receiver_configs, f, indent=4)
                    
                    logger.debug(f"Removed receiver configuration: {receiver_id}")
                
            except Exception as e:
                logger.error(f"Error removing receiver configuration: {e}")
                raise
    
    def get_receiver_configs(self) -> List[Dict]:
        """Get all receiver configurations"""
        with self.lock:
            return list(self.receiver_configs.values())
    
    def get_receiver_config(self, receiver_id: str) -> Optional[Dict]:
        """Get specific receiver configuration"""
        with self.lock:
            return self.receiver_configs.get(receiver_id)
    
    def validate_sender_config(self, config: Dict) -> List[str]:
        """
        Validate sender configuration
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Required fields
            required_fields = ['id', 'name', 'input', 'output']
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: {field}")
            
            # Validate input configuration
            if 'input' in config:
                input_config = config['input']
                required_input_fields = ['multicast_address', 'port']
                for field in required_input_fields:
                    if field not in input_config:
                        errors.append(f"Missing input field: {field}")
                
                # Validate multicast address format
                if 'multicast_address' in input_config:
                    addr = input_config['multicast_address']
                    if not self._validate_multicast_address(addr):
                        errors.append(f"Invalid multicast address: {addr}")
                
                # Validate port range
                if 'port' in input_config:
                    port = input_config['port']
                    if not (1024 <= port <= 65535):
                        errors.append(f"Invalid port range: {port} (must be 1024-65535)")
            
            # Validate output configuration
            if 'output' in config:
                output_config = config['output']
                required_output_fields = ['destination_address', 'destination_port']
                for field in required_output_fields:
                    if field not in output_config:
                        errors.append(f"Missing output field: {field}")
                
                # Validate destination port
                if 'destination_port' in output_config:
                    port = output_config['destination_port']
                    if not (1024 <= port <= 65535):
                        errors.append(f"Invalid destination port: {port}")
            
            # Validate codec configuration
            if 'codec' in config:
                codec_config = config['codec']
                if 'type' in codec_config:
                    codec_type = codec_config['type']
                    valid_codecs = self.system_config['audio']['supported_codecs']
                    if codec_type not in valid_codecs:
                        errors.append(f"Unsupported codec: {codec_type}")
        
        except Exception as e:
            errors.append(f"Configuration validation error: {e}")
        
        return errors
    
    def validate_receiver_config(self, config: Dict) -> List[str]:
        """
        Validate receiver configuration
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Required fields
            required_fields = ['id', 'name', 'input', 'output']
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: {field}")
            
            # Validate input configuration
            if 'input' in config:
                input_config = config['input']
                required_input_fields = ['port']
                for field in required_input_fields:
                    if field not in input_config:
                        errors.append(f"Missing input field: {field}")
                
                # Validate port range
                if 'port' in input_config:
                    port = input_config['port']
                    if not (1024 <= port <= 65535):
                        errors.append(f"Invalid input port: {port}")
            
            # Validate output configuration
            if 'output' in config:
                output_config = config['output']
                required_output_fields = ['multicast_address', 'port']
                for field in required_output_fields:
                    if field not in output_config:
                        errors.append(f"Missing output field: {field}")
                
                # Validate multicast address
                if 'multicast_address' in output_config:
                    addr = output_config['multicast_address']
                    if not self._validate_multicast_address(addr):
                        errors.append(f"Invalid output multicast address: {addr}")
                
                # Validate port range
                if 'port' in output_config:
                    port = output_config['port']
                    if not (1024 <= port <= 65535):
                        errors.append(f"Invalid output port: {port}")
        
        except Exception as e:
            errors.append(f"Configuration validation error: {e}")
        
        return errors
    
    def _validate_multicast_address(self, address: str) -> bool:
        """Validate multicast IP address"""
        try:
            import ipaddress
            ip = ipaddress.IPv4Address(address)
            # Multicast range: 224.0.0.0 to 239.255.255.255
            return ip.is_multicast
        except Exception:
            return False
    
    def create_example_configs(self):
        """Create example configurations for testing"""
        with self.lock:
            # Example sender configuration
            example_sender = {
                "id": "sender_001",
                "name": "Studio A Feed",
                "description": "Main studio audio feed",
                "input": {
                    "multicast_address": "239.1.1.1",
                    "port": 5004,
                    "interface": "0.0.0.0",
                    "format": "livewire+",
                    "sample_rate": 48000,
                    "bit_depth": 24,
                    "channels": 2
                },
                "output": {
                    "destination_address": "10.0.1.100",
                    "destination_port": 6000,
                    "protocol": "udp"
                },
                "codec": {
                    "type": "pcm",
                    "sample_rate": 48000,
                    "bit_depth": 24,
                    "channels": 2
                },
                "enabled": False,
                "created": datetime.now().isoformat()
            }
            
            # Example receiver configuration
            example_receiver = {
                "id": "receiver_001",
                "name": "Remote Studio Output",
                "description": "Audio output for remote studio",
                "input": {
                    "port": 6000,
                    "interface": "0.0.0.0",
                    "buffer_size": 1048576
                },
                "output": {
                    "multicast_address": "239.2.2.2",
                    "port": 5004,
                    "ttl": 1,
                    "format": "aes67",
                    "sample_rate": 48000,
                    "bit_depth": 24,
                    "channels": 2
                },
                "codec": {
                    "type": "pcm",
                    "sample_rate": 48000,
                    "bit_depth": 24,
                    "channels": 2
                },
                "enabled": False,
                "created": datetime.now().isoformat()
            }
            
            # Save example configurations
            self.save_sender_config(example_sender)
            self.save_receiver_config(example_receiver)
            
            logger.info("Created example configurations")
    
    def backup_configs(self, backup_dir: str = "config_backups"):
        """Create backup of all configurations"""
        try:
            import shutil
            from datetime import datetime
            
            # Create backup directory
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
            
            # Copy configuration directory
            shutil.copytree(self.config_dir, backup_path)
            
            logger.info(f"Configuration backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create configuration backup: {e}")
            raise
    
    def restore_configs(self, backup_path: str):
        """Restore configurations from backup"""
        try:
            import shutil
            
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup path not found: {backup_path}")
            
            # Backup current configs before restore
            current_backup = self.backup_configs()
            
            try:
                # Remove current config directory
                shutil.rmtree(self.config_dir)
                
                # Restore from backup
                shutil.copytree(backup_path, self.config_dir)
                
                # Reload configurations
                self.load_config()
                
                logger.info(f"Configurations restored from: {backup_path}")
                
            except Exception as e:
                # Restore the backup we just made
                shutil.rmtree(self.config_dir, ignore_errors=True)
                shutil.copytree(current_backup, self.config_dir)
                self.load_config()
                raise e
                
        except Exception as e:
            logger.error(f"Failed to restore configurations: {e}")
            raise
