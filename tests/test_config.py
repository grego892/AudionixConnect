"""
Tests for the AudionixConnect configuration module.
"""

import os
import json
import pytest
from audionix_connect.config import Config, load_config


def test_config_validation():
    """Test that configuration validation works correctly."""
    # Valid config
    valid_config = {
        "input": {
            "multicast_address": "239.192.0.1",
            "port": 5004,
            "format": "aes67"
        },
        "output": {
            "destination_address": "192.168.1.100",
            "destination_port": 5005,
            "encoding": "opus",
            "bitrate": 128000
        }
    }
    
    config = Config(**valid_config)
    assert config.input.multicast_address == "239.192.0.1"
    assert config.output.encoding == "opus"
    
    # Test invalid multicast address
    invalid_config = valid_config.copy()
    invalid_config["input"]["multicast_address"] = "192.168.1.1"  # Not a multicast address
    
    with pytest.raises(ValueError):
        Config(**invalid_config)
    
    # Test missing bitrate for opus
    invalid_config = valid_config.copy()
    invalid_config["output"]["bitrate"] = None
    
    with pytest.raises(ValueError):
        Config(**invalid_config)


def test_load_config(tmpdir):
    """Test loading configuration from a file."""
    # Create a temporary config file
    config = {
        "input": {
            "multicast_address": "239.192.0.1",
            "port": 5004,
            "format": "aes67"
        },
        "output": {
            "destination_address": "192.168.1.100",
            "destination_port": 5005,
            "encoding": "pcm"
        }
    }
    
    config_path = os.path.join(tmpdir, "test_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f)
    
    # Load the config
    loaded_config = load_config(config_path)
    
    # Verify it loaded correctly
    assert loaded_config.input.multicast_address == "239.192.0.1"
    assert loaded_config.output.encoding == "pcm"
    assert loaded_config.output.bitrate is None  # Not needed for PCM
    
    # Test loading non-existent file
    with pytest.raises(FileNotFoundError):
        load_config("non_existent_file.json")
