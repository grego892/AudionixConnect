/**
 * API Service - HTTP API communication
 * 
 * This service handles all HTTP API communication with the AudionixConnect backend.
 */

import axios from 'axios';

class ApiService {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
    
    // Create axios instance with default configuration
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        return response.data;
      },
      (error) => {
        console.error('API Error:', error);
        
        // Handle different error types
        if (error.response) {
          // Server responded with error status
          const errorMessage = error.response.data?.error || 'Server error';
          throw new Error(errorMessage);
        } else if (error.request) {
          // Request was made but no response received
          throw new Error('No response from server. Please check your connection.');
        } else {
          // Something else happened
          throw new Error(error.message || 'Request failed');
        }
      }
    );
  }

  // System Status
  async getSystemStatus() {
    return this.client.get('/status');
  }

  async getSystemHealth() {
    return this.client.get('/status/health');
  }

  async getNetworkStatus() {
    return this.client.get('/status/network');
  }

  async runDiagnostics() {
    return this.client.get('/status/diagnostics');
  }

  async getStreamOverview() {
    return this.client.get('/status/streams');
  }

  // System Configuration
  async getSystemConfig() {
    return this.client.get('/config');
  }

  async updateSystemConfig(config) {
    return this.client.post('/config', config);
  }

  // Senders
  async getSenders() {
    return this.client.get('/senders');
  }

  async getSender(senderId) {
    return this.client.get(`/senders/${senderId}`);
  }

  async createSender(senderConfig) {
    return this.client.post('/senders', senderConfig);
  }

  async updateSender(senderId, senderConfig) {
    return this.client.put(`/senders/${senderId}`, senderConfig);
  }

  async deleteSender(senderId) {
    return this.client.delete(`/senders/${senderId}`);
  }

  async startSender(senderId) {
    return this.client.post(`/senders/${senderId}/start`);
  }

  async stopSender(senderId) {
    return this.client.post(`/senders/${senderId}/stop`);
  }

  async restartSender(senderId) {
    return this.client.post(`/senders/${senderId}/restart`);
  }

  async getSenderStatus(senderId) {
    return this.client.get(`/senders/${senderId}/status`);
  }

  async startMultipleSenders(senderIds) {
    return this.client.post('/senders/bulk/start', { sender_ids: senderIds });
  }

  async stopMultipleSenders(senderIds) {
    return this.client.post('/senders/bulk/stop', { sender_ids: senderIds });
  }

  // Receivers
  async getReceivers() {
    return this.client.get('/receivers');
  }

  async getReceiver(receiverId) {
    return this.client.get(`/receivers/${receiverId}`);
  }

  async createReceiver(receiverConfig) {
    return this.client.post('/receivers', receiverConfig);
  }

  async updateReceiver(receiverId, receiverConfig) {
    return this.client.put(`/receivers/${receiverId}`, receiverConfig);
  }

  async deleteReceiver(receiverId) {
    return this.client.delete(`/receivers/${receiverId}`);
  }

  async startReceiver(receiverId) {
    return this.client.post(`/receivers/${receiverId}/start`);
  }

  async stopReceiver(receiverId) {
    return this.client.post(`/receivers/${receiverId}/stop`);
  }

  async restartReceiver(receiverId) {
    return this.client.post(`/receivers/${receiverId}/restart`);
  }

  async getReceiverStatus(receiverId) {
    return this.client.get(`/receivers/${receiverId}/status`);
  }

  async startMultipleReceivers(receiverIds) {
    return this.client.post('/receivers/bulk/start', { receiver_ids: receiverIds });
  }

  async stopMultipleReceivers(receiverIds) {
    return this.client.post('/receivers/bulk/stop', { receiver_ids: receiverIds });
  }

  // Utility methods
  async ping() {
    try {
      const response = await this.client.get('/status/health');
      return response.health?.status === 'healthy';
    } catch (error) {
      return false;
    }
  }

  // Configuration validation
  validateSenderConfig(config) {
    const errors = [];

    if (!config.name || config.name.trim() === '') {
      errors.push('Sender name is required');
    }

    if (!config.input) {
      errors.push('Input configuration is required');
    } else {
      if (!config.input.multicast_address) {
        errors.push('Input multicast address is required');
      }
      if (!config.input.port || config.input.port < 1024 || config.input.port > 65535) {
        errors.push('Input port must be between 1024 and 65535');
      }
    }

    if (!config.output) {
      errors.push('Output configuration is required');
    } else {
      if (!config.output.destination_address) {
        errors.push('Output destination address is required');
      }
      if (!config.output.destination_port || config.output.destination_port < 1024 || config.output.destination_port > 65535) {
        errors.push('Output destination port must be between 1024 and 65535');
      }
    }

    return errors;
  }

  validateReceiverConfig(config) {
    const errors = [];

    if (!config.name || config.name.trim() === '') {
      errors.push('Receiver name is required');
    }

    if (!config.input) {
      errors.push('Input configuration is required');
    } else {
      if (!config.input.port || config.input.port < 1024 || config.input.port > 65535) {
        errors.push('Input port must be between 1024 and 65535');
      }
    }

    if (!config.output) {
      errors.push('Output configuration is required');
    } else {
      if (!config.output.multicast_address) {
        errors.push('Output multicast address is required');
      }
      if (!config.output.port || config.output.port < 1024 || config.output.port > 65535) {
        errors.push('Output port must be between 1024 and 65535');
      }
    }

    return errors;
  }

  // Format helpers
  formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  formatBitrate(bps) {
    if (bps === 0) return '0 bps';
    const k = 1000; // Use 1000 for bitrates, not 1024
    const sizes = ['bps', 'kbps', 'Mbps', 'Gbps'];
    const i = Math.floor(Math.log(bps) / Math.log(k));
    return parseFloat((bps / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  formatUptime(seconds) {
    if (seconds < 60) {
      return `${Math.floor(seconds)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${minutes}m ${secs}s`;
    } else if (seconds < 86400) {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    } else {
      const days = Math.floor(seconds / 86400);
      const hours = Math.floor((seconds % 86400) / 3600);
      return `${days}d ${hours}h`;
    }
  }

  formatAudioLevel(dbfs) {
    if (dbfs <= -60) return 'Silent';
    if (dbfs >= -0.1) return 'CLIP!';
    return `${dbfs.toFixed(1)} dBFS`;
  }

  // Generate default configurations
  getDefaultSenderConfig() {
    return {
      name: '',
      description: '',
      input: {
        multicast_address: '239.1.1.1',
        port: 5004,
        interface: '0.0.0.0',
        format: 'livewire+',
        sample_rate: 48000,
        bit_depth: 24,
        channels: 2
      },
      output: {
        destination_address: '',
        destination_port: 6000,
        protocol: 'udp'
      },
      codec: {
        type: 'pcm',
        sample_rate: 48000,
        bit_depth: 24,
        channels: 2
      },
      enabled: false
    };
  }

  getDefaultReceiverConfig() {
    return {
      name: '',
      description: '',
      input: {
        port: 6000,
        interface: '0.0.0.0',
        buffer_size: 1048576
      },
      output: {
        multicast_address: '239.2.2.2',
        port: 5004,
        ttl: 1,
        format: 'aes67',
        sample_rate: 48000,
        bit_depth: 24,
        channels: 2
      },
      codec: {
        type: 'pcm',
        sample_rate: 48000,
        bit_depth: 24,
        channels: 2
      },
      enabled: false
    };
  }

  // Configuration Management
  async getConfiguration() {
    try {
      return await this.client.get('/config');
    } catch (error) {
      console.error('Error fetching configuration:', error);
      throw error;
    }
  }

  async updateConfiguration(config) {
    try {
      return await this.client.put('/config', config);
    } catch (error) {
      console.error('Error updating configuration:', error);
      throw error;
    }
  }

  async resetConfiguration() {
    try {
      return await this.client.post('/config/reset');
    } catch (error) {
      console.error('Error resetting configuration:', error);
      throw error;
    }
  }

  // Network and Diagnostics
  async getNetworkStatus() {
    try {
      return await this.client.get('/network/status');
    } catch (error) {
      console.error('Error fetching network status:', error);
      throw error;
    }
  }

  async runDiagnostics() {
    try {
      return await this.client.post('/diagnostics/run');
    } catch (error) {
      console.error('Error running diagnostics:', error);
      throw error;
    }
  }

  // Enhanced Status with detailed system information
  async getSystemStatus() {
    try {
      const response = await this.client.get('/status');
      return {
        ...response,
        resources: response.resources || {},
        streams: response.streams || {},
        system: response.system || {}
      };
    } catch (error) {
      console.error('Error fetching system status:', error);
      throw error;
    }
  }
}

// Create and export singleton instance
export const apiService = new ApiService();
