/**
 * Socket Service - Real-time WebSocket communication
 * 
 * This service handles real-time communication with the AudionixConnect backend
 * using Socket.IO for status updates, audio levels, and system notifications.
 */

import { io } from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.listeners = new Map();
    
    // Connection settings
    this.serverUrl = process.env.REACT_APP_SOCKET_URL || 'http://localhost:5000';
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    
    // Auto-reconnect settings
    this.autoReconnect = true;
    this.reconnectDelay = 1000; // Start with 1 second
    this.maxReconnectDelay = 30000; // Max 30 seconds
  }

  connect() {
    if (this.socket && this.socket.connected) {
      console.log('Socket already connected');
      return;
    }

    console.log('Connecting to AudionixConnect server...');

    this.socket = io(this.serverUrl, {
      transports: ['websocket', 'polling'],
      timeout: 5000,
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
      reconnectionDelayMax: this.maxReconnectDelay,
      randomizationFactor: 0.5,
    });

    this.setupEventHandlers();
  }

  setupEventHandlers() {
    if (!this.socket) return;

    // Connection events
    this.socket.on('connect', () => {
      console.log('Connected to AudionixConnect server');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000; // Reset delay
      this.emit('internal_connect');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('Disconnected from server:', reason);
      this.isConnected = false;
      this.emit('internal_disconnect', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.error('Connection error:', error);
      this.isConnected = false;
      
      // Exponential backoff for reconnection
      this.reconnectAttempts++;
      this.reconnectDelay = Math.min(
        this.reconnectDelay * 2,
        this.maxReconnectDelay
      );
      
      this.emit('internal_connect_error', error);
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log('Reconnected after', attemptNumber, 'attempts');
      this.emit('internal_reconnect', attemptNumber);
    });

    this.socket.on('reconnecting', (attemptNumber) => {
      console.log('Attempting to reconnect...', attemptNumber);
      this.emit('internal_reconnecting', attemptNumber);
    });

    this.socket.on('reconnect_error', (error) => {
      console.error('Reconnection failed:', error);
      this.emit('internal_reconnect_error', error);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('Failed to reconnect after maximum attempts');
      this.emit('internal_reconnect_failed');
    });

    // Server events
    this.socket.on('status_update', (data) => {
      this.emit('status_update', data);
    });

    this.socket.on('audio_levels', (data) => {
      this.emit('audio_levels', data);
    });

    this.socket.on('error', (error) => {
      console.error('Server error:', error);
      this.emit('error', error);
    });

    this.socket.on('notification', (notification) => {
      this.emit('notification', notification);
    });

    // Stream events
    this.socket.on('stream_started', (data) => {
      this.emit('stream_started', data);
    });

    this.socket.on('stream_stopped', (data) => {
      this.emit('stream_stopped', data);
    });

    this.socket.on('stream_error', (data) => {
      this.emit('stream_error', data);
    });

    // System events
    this.socket.on('system_alert', (data) => {
      this.emit('system_alert', data);
    });

    this.socket.on('config_changed', (data) => {
      this.emit('config_changed', data);
    });
  }

  disconnect() {
    if (this.socket) {
      console.log('Disconnecting from server...');
      this.autoReconnect = false;
      this.socket.disconnect();
      this.socket = null;
    }
    this.isConnected = false;
    this.listeners.clear();
  }

  // Event listener management
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);

    // Handle internal events
    if (event === 'connect') {
      this.on('internal_connect', callback);
    } else if (event === 'disconnect') {
      this.on('internal_disconnect', callback);
    } else if (event === 'reconnecting') {
      this.on('internal_reconnecting', callback);
    } else if (event === 'connect_error') {
      this.on('internal_connect_error', callback);
    }
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
      if (callbacks.length === 0) {
        this.listeners.delete(event);
      }
    }
  }

  emit(event, data) {
    // Handle internal events
    if (event.startsWith('internal_')) {
      const externalEvent = event.replace('internal_', '');
      if (this.listeners.has(externalEvent)) {
        this.listeners.get(externalEvent).forEach(callback => {
          try {
            callback(data);
          } catch (error) {
            console.error('Error in event callback:', error);
          }
        });
      }
      return;
    }

    // Handle custom events
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in event callback:', error);
        }
      });
    }

    // Send to server if connected
    if (this.socket && this.isConnected) {
      this.socket.emit(event, data);
    }
  }

  // Convenience methods for common operations
  requestStatus() {
    this.emit('request_status');
  }

  requestStreamUpdate(streamId) {
    this.emit('request_stream_update', { stream_id: streamId });
  }

  subscribeToAudioLevels(streamIds = []) {
    this.emit('subscribe_audio_levels', { stream_ids: streamIds });
  }

  unsubscribeFromAudioLevels(streamIds = []) {
    this.emit('unsubscribe_audio_levels', { stream_ids: streamIds });
  }

  // Connection status
  getConnectionStatus() {
    if (!this.socket) return 'disconnected';
    
    if (this.socket.connected) {
      return 'connected';
    } else if (this.socket.disconnected) {
      return 'disconnected';
    } else {
      return 'connecting';
    }
  }

  isSocketConnected() {
    return this.isConnected && this.socket && this.socket.connected;
  }

  // Manual reconnection
  reconnect() {
    if (this.socket) {
      console.log('Manual reconnection triggered');
      this.socket.connect();
    } else {
      this.connect();
    }
  }

  // Get connection statistics
  getConnectionStats() {
    if (!this.socket) {
      return {
        connected: false,
        transport: null,
        reconnectAttempts: this.reconnectAttempts,
        lastError: null
      };
    }

    return {
      connected: this.socket.connected,
      transport: this.socket.io.engine?.transport?.name || null,
      reconnectAttempts: this.reconnectAttempts,
      id: this.socket.id,
      url: this.serverUrl
    };
  }

  // Ping the server
  ping() {
    return new Promise((resolve) => {
      if (!this.isSocketConnected()) {
        resolve(false);
        return;
      }

      const timeout = setTimeout(() => {
        resolve(false);
      }, 5000);

      this.socket.emit('ping', Date.now(), (response) => {
        clearTimeout(timeout);
        resolve(true);
      });
    });
  }

  // Send heartbeat
  startHeartbeat(interval = 30000) {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    this.heartbeatInterval = setInterval(() => {
      if (this.isSocketConnected()) {
        this.emit('heartbeat', { timestamp: Date.now() });
      }
    }, interval);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // Error handling
  handleError(error, context = '') {
    console.error(`Socket error ${context}:`, error);
    this.emit('error', { error, context });
  }

  // Cleanup
  cleanup() {
    this.stopHeartbeat();
    this.disconnect();
  }
}

// Create and export singleton instance
export const socketService = new SocketService();
