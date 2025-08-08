"""
Receiver API - REST endpoints for managing audio receivers

This module provides REST API endpoints for creating, configuring,
and managing audio receiver instances.
"""

from flask import Blueprint, request, jsonify, current_app
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

receiver_bp = Blueprint('receivers', __name__)

def get_stream_manager():
    """Get stream manager instance from app context"""
    return current_app.config.get('stream_manager')

def get_config_manager():
    """Get config manager instance from app context"""
    return current_app.config.get('config_manager')

@receiver_bp.route('', methods=['GET'])
def list_receivers():
    """Get list of all receivers"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        receivers = stream_manager.get_receiver_status()
        
        return jsonify({
            'success': True,
            'receivers': receivers,
            'count': len(receivers)
        })
        
    except Exception as e:
        logger.error(f"Error listing receivers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@receiver_bp.route('', methods=['POST'])
def create_receiver():
    """Create a new receiver"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Generate ID if not provided
        if 'id' not in data:
            data['id'] = f"receiver_{uuid.uuid4().hex[:8]}"
        
        # Add creation timestamp
        data['created'] = datetime.now().isoformat()
        
        # Get managers
        stream_manager = get_stream_manager()
        config_manager = get_config_manager()
        
        if not stream_manager or not config_manager:
            return jsonify({'success': False, 'error': 'Managers not available'}), 500
        
        # Validate configuration
        validation_errors = config_manager.validate_receiver_config(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Configuration validation failed',
                'validation_errors': validation_errors
            }), 400
        
        # Create receiver
        success = stream_manager.create_receiver(data)
        if not success:
            return jsonify({'success': False, 'error': 'Failed to create receiver'}), 500
        
        logger.info(f"Created receiver: {data['id']} - {data['name']}")
        
        return jsonify({
            'success': True,
            'receiver_id': data['id'],
            'message': 'Receiver created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating receiver: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@receiver_bp.route('/<receiver_id>', methods=['GET'])
def get_receiver(receiver_id):
    """Get specific receiver details"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        if receiver_id not in stream_manager.receivers:
            return jsonify({'success': False, 'error': 'Receiver not found'}), 404
        
        receiver = stream_manager.receivers[receiver_id]
        status = receiver.get_status()
        
        return jsonify({
            'success': True,
            'receiver': status
        })
        
    except Exception as e:
        logger.error(f"Error getting receiver {receiver_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@receiver_bp.route('/<receiver_id>', methods=['PUT'])
def update_receiver(receiver_id):
    """Update receiver configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        stream_manager = get_stream_manager()
        config_manager = get_config_manager()
        
        if not stream_manager or not config_manager:
            return jsonify({'success': False, 'error': 'Managers not available'}), 500
        
        if receiver_id not in stream_manager.receivers:
            return jsonify({'success': False, 'error': 'Receiver not found'}), 404
        
        # Ensure ID matches
        data['id'] = receiver_id
        data['last_modified'] = datetime.now().isoformat()
        
        # Validate configuration
        validation_errors = config_manager.validate_receiver_config(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Configuration validation failed',
                'validation_errors': validation_errors
            }), 400
        
        # Stop receiver if running
        receiver = stream_manager.receivers[receiver_id]
        was_active = receiver.active
        if was_active:
            receiver.stop()
        
        # Remove and recreate receiver with new configuration
        stream_manager.remove_receiver(receiver_id)
        success = stream_manager.create_receiver(data)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to update receiver'}), 500
        
        # Restart if it was active
        if was_active:
            stream_manager.start_receiver(receiver_id)
        
        logger.info(f"Updated receiver: {receiver_id}")
        
        return jsonify({
            'success': True,
            'message': 'Receiver updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating receiver {receiver_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@receiver_bp.route('/<receiver_id>', methods=['DELETE'])
def delete_receiver(receiver_id):
    """Delete a receiver"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        if receiver_id not in stream_manager.receivers:
            return jsonify({'success': False, 'error': 'Receiver not found'}), 404
        
        # Remove receiver
        success = stream_manager.remove_receiver(receiver_id)
        if not success:
            return jsonify({'success': False, 'error': 'Failed to delete receiver'}), 500
        
        logger.info(f"Deleted receiver: {receiver_id}")
        
        return jsonify({
            'success': True,
            'message': 'Receiver deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting receiver {receiver_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@receiver_bp.route('/<receiver_id>/start', methods=['POST'])
def start_receiver(receiver_id):
    """Start a receiver"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        if receiver_id not in stream_manager.receivers:
            return jsonify({'success': False, 'error': 'Receiver not found'}), 404
        
        success = stream_manager.start_receiver(receiver_id)
        if not success:
            return jsonify({'success': False, 'error': 'Failed to start receiver'}), 500
        
        logger.info(f"Started receiver: {receiver_id}")
        
        return jsonify({
            'success': True,
            'message': 'Receiver started successfully'
        })
        
    except Exception as e:
        logger.error(f"Error starting receiver {receiver_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@receiver_bp.route('/<receiver_id>/stop', methods=['POST'])
def stop_receiver(receiver_id):
    """Stop a receiver"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        if receiver_id not in stream_manager.receivers:
            return jsonify({'success': False, 'error': 'Receiver not found'}), 404
        
        success = stream_manager.stop_receiver(receiver_id)
        if not success:
            return jsonify({'success': False, 'error': 'Failed to stop receiver'}), 500
        
        logger.info(f"Stopped receiver: {receiver_id}")
        
        return jsonify({
            'success': True,
            'message': 'Receiver stopped successfully'
        })
        
    except Exception as e:
        logger.error(f"Error stopping receiver {receiver_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@receiver_bp.route('/<receiver_id>/restart', methods=['POST'])
def restart_receiver(receiver_id):
    """Restart a receiver"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        if receiver_id not in stream_manager.receivers:
            return jsonify({'success': False, 'error': 'Receiver not found'}), 404
        
        # Stop then start
        stream_manager.stop_receiver(receiver_id)
        success = stream_manager.start_receiver(receiver_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to restart receiver'}), 500
        
        logger.info(f"Restarted receiver: {receiver_id}")
        
        return jsonify({
            'success': True,
            'message': 'Receiver restarted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error restarting receiver {receiver_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@receiver_bp.route('/<receiver_id>/status', methods=['GET'])
def get_receiver_status(receiver_id):
    """Get detailed receiver status"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        if receiver_id not in stream_manager.receivers:
            return jsonify({'success': False, 'error': 'Receiver not found'}), 404
        
        receiver = stream_manager.receivers[receiver_id]
        status = receiver.get_status()
        
        # Add additional status information
        from audio.audio_processor import AudioProcessor
        audio_processor = AudioProcessor()
        
        detailed_status = status.copy()
        detailed_status.update({
            'stream_statistics': audio_processor.get_stream_statistics(receiver_id),
            'silence_detected': audio_processor.detect_silence(receiver_id),
            'clipping_detected': audio_processor.detect_clipping(receiver_id)
        })
        
        return jsonify({
            'success': True,
            'status': detailed_status
        })
        
    except Exception as e:
        logger.error(f"Error getting receiver status {receiver_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@receiver_bp.route('/bulk/start', methods=['POST'])
def start_multiple_receivers():
    """Start multiple receivers"""
    try:
        data = request.get_json()
        if not data or 'receiver_ids' not in data:
            return jsonify({'success': False, 'error': 'No receiver IDs provided'}), 400
        
        receiver_ids = data['receiver_ids']
        stream_manager = get_stream_manager()
        
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        results = {}
        success_count = 0
        
        for receiver_id in receiver_ids:
            try:
                if receiver_id in stream_manager.receivers:
                    success = stream_manager.start_receiver(receiver_id)
                    results[receiver_id] = {'success': success}
                    if success:
                        success_count += 1
                else:
                    results[receiver_id] = {'success': False, 'error': 'Receiver not found'}
            except Exception as e:
                results[receiver_id] = {'success': False, 'error': str(e)}
        
        logger.info(f"Bulk start: {success_count}/{len(receiver_ids)} receivers started")
        
        return jsonify({
            'success': True,
            'results': results,
            'success_count': success_count,
            'total_count': len(receiver_ids)
        })
        
    except Exception as e:
        logger.error(f"Error in bulk start: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@receiver_bp.route('/bulk/stop', methods=['POST'])
def stop_multiple_receivers():
    """Stop multiple receivers"""
    try:
        data = request.get_json()
        if not data or 'receiver_ids' not in data:
            return jsonify({'success': False, 'error': 'No receiver IDs provided'}), 400
        
        receiver_ids = data['receiver_ids']
        stream_manager = get_stream_manager()
        
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        results = {}
        success_count = 0
        
        for receiver_id in receiver_ids:
            try:
                if receiver_id in stream_manager.receivers:
                    success = stream_manager.stop_receiver(receiver_id)
                    results[receiver_id] = {'success': success}
                    if success:
                        success_count += 1
                else:
                    results[receiver_id] = {'success': False, 'error': 'Receiver not found'}
            except Exception as e:
                results[receiver_id] = {'success': False, 'error': str(e)}
        
        logger.info(f"Bulk stop: {success_count}/{len(receiver_ids)} receivers stopped")
        
        return jsonify({
            'success': True,
            'results': results,
            'success_count': success_count,
            'total_count': len(receiver_ids)
        })
        
    except Exception as e:
        logger.error(f"Error in bulk stop: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
