"""
Sender API - REST endpoints for managing audio senders

This module provides REST API endpoints for creating, configuring,
and managing audio sender instances.
"""

from flask import Blueprint, request, jsonify, current_app
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

sender_bp = Blueprint('senders', __name__)

def get_stream_manager():
    """Get stream manager instance from app context"""
    return current_app.config.get('stream_manager')

def get_config_manager():
    """Get config manager instance from app context"""
    return current_app.config.get('config_manager')

@sender_bp.route('', methods=['GET'])
def list_senders():
    """Get list of all senders"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        senders = stream_manager.get_sender_status()
        
        return jsonify({
            'success': True,
            'senders': senders,
            'count': len(senders)
        })
        
    except Exception as e:
        logger.error(f"Error listing senders: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sender_bp.route('', methods=['POST'])
def create_sender():
    """Create a new sender"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Generate ID if not provided
        if 'id' not in data:
            data['id'] = f"sender_{uuid.uuid4().hex[:8]}"
        
        # Add creation timestamp
        data['created'] = datetime.now().isoformat()
        
        # Get managers
        stream_manager = get_stream_manager()
        config_manager = get_config_manager()
        
        if not stream_manager or not config_manager:
            return jsonify({'success': False, 'error': 'Managers not available'}), 500
        
        # Validate configuration
        validation_errors = config_manager.validate_sender_config(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Configuration validation failed',
                'validation_errors': validation_errors
            }), 400
        
        # Create sender
        success = stream_manager.create_sender(data)
        if not success:
            return jsonify({'success': False, 'error': 'Failed to create sender'}), 500
        
        logger.info(f"Created sender: {data['id']} - {data['name']}")
        
        return jsonify({
            'success': True,
            'sender_id': data['id'],
            'message': 'Sender created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating sender: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sender_bp.route('/<sender_id>', methods=['GET'])
def get_sender(sender_id):
    """Get specific sender details"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        if sender_id not in stream_manager.senders:
            return jsonify({'success': False, 'error': 'Sender not found'}), 404
        
        sender = stream_manager.senders[sender_id]
        status = sender.get_status()
        
        return jsonify({
            'success': True,
            'sender': status
        })
        
    except Exception as e:
        logger.error(f"Error getting sender {sender_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sender_bp.route('/<sender_id>', methods=['PUT'])
def update_sender(sender_id):
    """Update sender configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        stream_manager = get_stream_manager()
        config_manager = get_config_manager()
        
        if not stream_manager or not config_manager:
            return jsonify({'success': False, 'error': 'Managers not available'}), 500
        
        if sender_id not in stream_manager.senders:
            return jsonify({'success': False, 'error': 'Sender not found'}), 404
        
        # Ensure ID matches
        data['id'] = sender_id
        data['last_modified'] = datetime.now().isoformat()
        
        # Validate configuration
        validation_errors = config_manager.validate_sender_config(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Configuration validation failed',
                'validation_errors': validation_errors
            }), 400
        
        # Stop sender if running
        sender = stream_manager.senders[sender_id]
        was_active = sender.active
        if was_active:
            sender.stop()
        
        # Remove and recreate sender with new configuration
        stream_manager.remove_sender(sender_id)
        success = stream_manager.create_sender(data)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to update sender'}), 500
        
        # Restart if it was active
        if was_active:
            stream_manager.start_sender(sender_id)
        
        logger.info(f"Updated sender: {sender_id}")
        
        return jsonify({
            'success': True,
            'message': 'Sender updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating sender {sender_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sender_bp.route('/<sender_id>', methods=['DELETE'])
def delete_sender(sender_id):
    """Delete a sender"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        if sender_id not in stream_manager.senders:
            return jsonify({'success': False, 'error': 'Sender not found'}), 404
        
        # Remove sender
        success = stream_manager.remove_sender(sender_id)
        if not success:
            return jsonify({'success': False, 'error': 'Failed to delete sender'}), 500
        
        logger.info(f"Deleted sender: {sender_id}")
        
        return jsonify({
            'success': True,
            'message': 'Sender deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting sender {sender_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sender_bp.route('/<sender_id>/start', methods=['POST'])
def start_sender(sender_id):
    """Start a sender"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        if sender_id not in stream_manager.senders:
            return jsonify({'success': False, 'error': 'Sender not found'}), 404
        
        success = stream_manager.start_sender(sender_id)
        if not success:
            return jsonify({'success': False, 'error': 'Failed to start sender'}), 500
        
        logger.info(f"Started sender: {sender_id}")
        
        return jsonify({
            'success': True,
            'message': 'Sender started successfully'
        })
        
    except Exception as e:
        logger.error(f"Error starting sender {sender_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sender_bp.route('/<sender_id>/stop', methods=['POST'])
def stop_sender(sender_id):
    """Stop a sender"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        if sender_id not in stream_manager.senders:
            return jsonify({'success': False, 'error': 'Sender not found'}), 404
        
        success = stream_manager.stop_sender(sender_id)
        if not success:
            return jsonify({'success': False, 'error': 'Failed to stop sender'}), 500
        
        logger.info(f"Stopped sender: {sender_id}")
        
        return jsonify({
            'success': True,
            'message': 'Sender stopped successfully'
        })
        
    except Exception as e:
        logger.error(f"Error stopping sender {sender_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sender_bp.route('/<sender_id>/restart', methods=['POST'])
def restart_sender(sender_id):
    """Restart a sender"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        if sender_id not in stream_manager.senders:
            return jsonify({'success': False, 'error': 'Sender not found'}), 404
        
        # Stop then start
        stream_manager.stop_sender(sender_id)
        success = stream_manager.start_sender(sender_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to restart sender'}), 500
        
        logger.info(f"Restarted sender: {sender_id}")
        
        return jsonify({
            'success': True,
            'message': 'Sender restarted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error restarting sender {sender_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sender_bp.route('/<sender_id>/status', methods=['GET'])
def get_sender_status(sender_id):
    """Get detailed sender status"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        if sender_id not in stream_manager.senders:
            return jsonify({'success': False, 'error': 'Sender not found'}), 404
        
        sender = stream_manager.senders[sender_id]
        status = sender.get_status()
        
        # Add additional status information
        from audio.audio_processor import AudioProcessor
        audio_processor = AudioProcessor()
        
        detailed_status = status.copy()
        detailed_status.update({
            'stream_statistics': audio_processor.get_stream_statistics(sender_id),
            'silence_detected': audio_processor.detect_silence(sender_id),
            'clipping_detected': audio_processor.detect_clipping(sender_id)
        })
        
        return jsonify({
            'success': True,
            'status': detailed_status
        })
        
    except Exception as e:
        logger.error(f"Error getting sender status {sender_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sender_bp.route('/bulk/start', methods=['POST'])
def start_multiple_senders():
    """Start multiple senders"""
    try:
        data = request.get_json()
        if not data or 'sender_ids' not in data:
            return jsonify({'success': False, 'error': 'No sender IDs provided'}), 400
        
        sender_ids = data['sender_ids']
        stream_manager = get_stream_manager()
        
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        results = {}
        success_count = 0
        
        for sender_id in sender_ids:
            try:
                if sender_id in stream_manager.senders:
                    success = stream_manager.start_sender(sender_id)
                    results[sender_id] = {'success': success}
                    if success:
                        success_count += 1
                else:
                    results[sender_id] = {'success': False, 'error': 'Sender not found'}
            except Exception as e:
                results[sender_id] = {'success': False, 'error': str(e)}
        
        logger.info(f"Bulk start: {success_count}/{len(sender_ids)} senders started")
        
        return jsonify({
            'success': True,
            'results': results,
            'success_count': success_count,
            'total_count': len(sender_ids)
        })
        
    except Exception as e:
        logger.error(f"Error in bulk start: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sender_bp.route('/bulk/stop', methods=['POST'])
def stop_multiple_senders():
    """Stop multiple senders"""
    try:
        data = request.get_json()
        if not data or 'sender_ids' not in data:
            return jsonify({'success': False, 'error': 'No sender IDs provided'}), 400
        
        sender_ids = data['sender_ids']
        stream_manager = get_stream_manager()
        
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        results = {}
        success_count = 0
        
        for sender_id in sender_ids:
            try:
                if sender_id in stream_manager.senders:
                    success = stream_manager.stop_sender(sender_id)
                    results[sender_id] = {'success': success}
                    if success:
                        success_count += 1
                else:
                    results[sender_id] = {'success': False, 'error': 'Sender not found'}
            except Exception as e:
                results[sender_id] = {'success': False, 'error': str(e)}
        
        logger.info(f"Bulk stop: {success_count}/{len(sender_ids)} senders stopped")
        
        return jsonify({
            'success': True,
            'results': results,
            'success_count': success_count,
            'total_count': len(sender_ids)
        })
        
    except Exception as e:
        logger.error(f"Error in bulk stop: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
