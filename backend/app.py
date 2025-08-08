"""
AudionixConnect - Professional Audio Streaming Management System
Main Flask Application

This module provides the main Flask application for AudionixConnect,
handling HTTP requests, WebSocket connections for real-time updates,
and coordinating audio stream management.
"""

from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import os
import threading
import time
from datetime import datetime
import logging

from audio.stream_manager import StreamManager
from audio.audio_processor import AudioProcessor
from config.config_manager import ConfigManager
from api.sender_api import sender_bp
from api.receiver_api import receiver_bp
from api.status_api import status_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'audionix-connect-secret-key-2025'

# Enable CORS for frontend integration
CORS(app, origins=["http://localhost:3000", "http://localhost:3001"])

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000", "http://localhost:3001"])

# Initialize core components
config_manager = ConfigManager()
stream_manager = StreamManager(config_manager)
audio_processor = AudioProcessor()

# Register API blueprints
app.register_blueprint(sender_bp, url_prefix='/api/senders')
app.register_blueprint(receiver_bp, url_prefix='/api/receivers')
app.register_blueprint(status_bp, url_prefix='/api/status')

class AudionixConnectApp:
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.last_update = {}
        
    def start_monitoring(self):
        """Start real-time monitoring thread"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Real-time monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Real-time monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop for real-time updates"""
        while self.running:
            try:
                # Get current status from stream manager
                status_data = {
                    'timestamp': datetime.now().isoformat(),
                    'senders': stream_manager.get_sender_status(),
                    'receivers': stream_manager.get_receiver_status(),
                    'system': {
                        'active_streams': stream_manager.get_active_stream_count(),
                        'total_bandwidth': stream_manager.get_total_bandwidth(),
                        'uptime': stream_manager.get_uptime()
                    }
                }
                
                # Emit updates to connected clients
                socketio.emit('status_update', status_data)
                
                # Get audio levels if available
                audio_levels = audio_processor.get_current_levels()
                if audio_levels:
                    socketio.emit('audio_levels', audio_levels)
                
                time.sleep(0.1)  # 10Hz update rate
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1)

# Create application instance
audionix_app = AudionixConnectApp()

@app.route('/')
def index():
    """Serve main application page"""
    return jsonify({
        'message': 'AudionixConnect API Server',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'senders': '/api/senders',
            'receivers': '/api/receivers',
            'status': '/api/status',
            'websocket': '/socket.io'
        }
    })

@app.route('/api/config', methods=['GET'])
def get_system_config():
    """Get current system configuration"""
    try:
        config = config_manager.get_system_config()
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        logger.error(f"Error getting system config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config', methods=['POST'])
def update_system_config():
    """Update system configuration"""
    try:
        new_config = request.get_json()
        config_manager.update_system_config(new_config)
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating system config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to AudionixConnect'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('request_status')
def handle_status_request():
    """Handle manual status request"""
    try:
        status_data = {
            'timestamp': datetime.now().isoformat(),
            'senders': stream_manager.get_sender_status(),
            'receivers': stream_manager.get_receiver_status(),
            'system': {
                'active_streams': stream_manager.get_active_stream_count(),
                'total_bandwidth': stream_manager.get_total_bandwidth(),
                'uptime': stream_manager.get_uptime()
            }
        }
        emit('status_update', status_data)
    except Exception as e:
        logger.error(f"Error handling status request: {e}")
        emit('error', {'message': str(e)})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    try:
        # Initialize system
        logger.info("Starting AudionixConnect...")
        
        # Load configuration
        config_manager.load_config()
        
        # Initialize stream manager
        stream_manager.initialize()
        
        # Start monitoring
        audionix_app.start_monitoring()
        
        # Start Flask-SocketIO server
        logger.info("AudionixConnect server starting on http://0.0.0.0:5000")
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        logger.info("Shutting down AudionixConnect...")
    except Exception as e:
        logger.error(f"Failed to start AudionixConnect: {e}")
    finally:
        # Cleanup
        audionix_app.stop_monitoring()
        stream_manager.shutdown()
        logger.info("AudionixConnect stopped")
