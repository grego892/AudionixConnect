"""
Configuration module for AudionixConnect.
"""

import json
import os
from pydantic import BaseModel, validator
from typing import Optional, Literal


class InputConfig(BaseModel):
    """Input stream configuration."""
    multicast_address: str
    port: int
    format: Literal["livewire", "aes67"]
    
    @validator('port')
    def validate_port(cls, v):
        if not 1024 <= v <= 65535:
            raise ValueError('Port must be between 1024 and 65535')
        return v
    
    @validator('multicast_address')
    def validate_multicast(cls, v):
        # Simple validation for multicast address
        octets = v.split('.')
        if len(octets) != 4:
            raise ValueError('Invalid IP address format')
        if not (224 <= int(octets[0]) <= 239):
            raise ValueError('Not a valid multicast address')
        return v


class OutputConfig(BaseModel):
    """Output stream configuration."""
    destination_address: str
    destination_port: int
    encoding: Literal["pcm", "opus"]
    bitrate: Optional[int] = None
    
    @validator('bitrate')
    def validate_bitrate(cls, v, values):
        if values.get('encoding') == 'opus' and (v is None or v <= 0):
            raise ValueError('Bitrate must be specified and positive for Opus encoding')
        return v
    
    @validator('destination_port')
    def validate_port(cls, v):
        if not 1024 <= v <= 65535:
            raise ValueError('Port must be between 1024 and 65535')
        return v


class Config(BaseModel):
    """Main application configuration."""
    input: InputConfig
    output: OutputConfig


def load_config(config_path: str) -> Config:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the JSON configuration file
        
    Returns:
        Config object with validated settings
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If the config file contains invalid settings
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    return Config(**config_data)
