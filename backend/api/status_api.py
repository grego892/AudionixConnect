"""
Status API - System status and monitoring endpoints

This module provides REST API endpoints for system status monitoring,
health checks, and network diagnostics.
"""

from flask import Blueprint, request, jsonify, current_app
import psutil
import socket
import time
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

status_bp = Blueprint('status', __name__)

def get_stream_manager():
    """Get stream manager instance from app context"""
    return current_app.config.get('stream_manager')

def get_config_manager():
    """Get config manager instance from app context"""
    return current_app.config.get('config_manager')

@status_bp.route('', methods=['GET'])
def get_system_status():
    """Get comprehensive system status"""
    try:
        stream_manager = get_stream_manager()
        config_manager = get_config_manager()
        
        if not stream_manager or not config_manager:
            return jsonify({'success': False, 'error': 'Managers not available'}), 500
        
        # System information
        system_info = {
            'timestamp': datetime.now().isoformat(),
            'uptime': stream_manager.get_uptime(),
            'version': '1.0.0',
            'hostname': socket.gethostname(),
            'platform': {
                'system': os.name,
                'python_version': f"{psutil.python_version()}" if hasattr(psutil, 'python_version') else "Unknown"
            }
        }
        
        # Resource usage
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            resources = {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                }
            }
        except Exception as e:
            logger.warning(f"Could not get system resources: {e}")
            resources = {'error': 'System resource monitoring unavailable'}
        
        # Stream statistics
        senders = stream_manager.get_sender_status()
        receivers = stream_manager.get_receiver_status()
        
        active_senders = sum(1 for s in senders if s.get('active', False))
        active_receivers = sum(1 for r in receivers if r.get('active', False))
        
        stream_stats = {
            'senders': {
                'total': len(senders),
                'active': active_senders,
                'inactive': len(senders) - active_senders
            },
            'receivers': {
                'total': len(receivers),
                'active': active_receivers,
                'inactive': len(receivers) - active_receivers
            },
            'total_streams': active_senders + active_receivers,
            'estimated_bandwidth_mbps': stream_manager.get_total_bandwidth()
        }
        
        # Network information
        network_info = get_network_interfaces()
        
        return jsonify({
            'success': True,
            'system': system_info,
            'resources': resources,
            'streams': stream_stats,
            'network': network_info,
            'senders': senders,
            'receivers': receivers
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@status_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    try:
        stream_manager = get_stream_manager()
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime': stream_manager.get_uptime() if stream_manager else 0,
            'components': {
                'stream_manager': stream_manager is not None,
                'config_manager': get_config_manager() is not None
            }
        }
        
        # Check if any components are failing
        if not all(health_status['components'].values()):
            health_status['status'] = 'degraded'
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return jsonify({
            'success': True,
            'health': health_status
        }), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'health': {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        }), 503

@status_bp.route('/streams', methods=['GET'])
def get_stream_overview():
    """Get stream overview with statistics"""
    try:
        stream_manager = get_stream_manager()
        if not stream_manager:
            return jsonify({'success': False, 'error': 'Stream manager not available'}), 500
        
        senders = stream_manager.get_sender_status()
        receivers = stream_manager.get_receiver_status()
        
        # Calculate statistics
        current_time = time.time()
        
        sender_stats = []
        for sender in senders:
            stats = sender.get('stats', {})
            runtime = current_time - (stats.get('start_time', current_time) if stats.get('start_time') else current_time)
            
            sender_stats.append({
                'id': sender['id'],
                'name': sender['name'],
                'active': sender['active'],
                'packets_received': stats.get('packets_received', 0),
                'packets_sent': stats.get('packets_sent', 0),
                'bytes_received': stats.get('bytes_received', 0),
                'bytes_sent': stats.get('bytes_sent', 0),
                'errors': stats.get('errors', 0),
                'runtime': runtime,
                'audio_levels': sender.get('audio_levels', {'left': -60, 'right': -60})
            })
        
        receiver_stats = []
        for receiver in receivers:
            stats = receiver.get('stats', {})
            runtime = current_time - (stats.get('start_time', current_time) if stats.get('start_time') else current_time)
            
            receiver_stats.append({
                'id': receiver['id'],
                'name': receiver['name'],
                'active': receiver['active'],
                'packets_received': stats.get('packets_received', 0),
                'packets_sent': stats.get('packets_sent', 0),
                'bytes_received': stats.get('bytes_received', 0),
                'bytes_sent': stats.get('bytes_sent', 0),
                'errors': stats.get('errors', 0),
                'runtime': runtime,
                'audio_levels': receiver.get('audio_levels', {'left': -60, 'right': -60})
            })
        
        return jsonify({
            'success': True,
            'overview': {
                'timestamp': datetime.now().isoformat(),
                'total_streams': len(sender_stats) + len(receiver_stats),
                'active_streams': sum(1 for s in sender_stats if s['active']) + sum(1 for r in receiver_stats if r['active']),
                'total_packets': sum(s['packets_received'] + s['packets_sent'] for s in sender_stats + receiver_stats),
                'total_bytes': sum(s['bytes_received'] + s['bytes_sent'] for s in sender_stats + receiver_stats),
                'total_errors': sum(s['errors'] for s in sender_stats + receiver_stats)
            },
            'senders': sender_stats,
            'receivers': receiver_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting stream overview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@status_bp.route('/network', methods=['GET'])
def get_network_status():
    """Get network interface and connectivity status"""
    try:
        network_info = get_network_interfaces()
        
        # Test connectivity to common destinations
        connectivity_tests = []
        test_addresses = [
            ('8.8.8.8', 53),  # Google DNS
            ('1.1.1.1', 53),  # Cloudflare DNS
        ]
        
        for address, port in test_addresses:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((address, port))
                sock.close()
                
                connectivity_tests.append({
                    'destination': f"{address}:{port}",
                    'reachable': result == 0,
                    'service': 'DNS'
                })
            except Exception as e:
                connectivity_tests.append({
                    'destination': f"{address}:{port}",
                    'reachable': False,
                    'error': str(e),
                    'service': 'DNS'
                })
        
        return jsonify({
            'success': True,
            'network': {
                'interfaces': network_info,
                'connectivity': connectivity_tests,
                'hostname': socket.gethostname(),
                'fqdn': socket.getfqdn()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting network status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@status_bp.route('/diagnostics', methods=['GET'])
def run_diagnostics():
    """Run system diagnostics"""
    try:
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        
        stream_manager = get_stream_manager()
        config_manager = get_config_manager()
        
        # Test 1: Component availability
        diagnostics['tests'].append({
            'name': 'Component Availability',
            'status': 'pass' if (stream_manager and config_manager) else 'fail',
            'details': {
                'stream_manager': stream_manager is not None,
                'config_manager': config_manager is not None
            }
        })
        
        # Test 2: Configuration validity
        if config_manager:
            try:
                system_config = config_manager.get_system_config()
                config_test = {
                    'name': 'Configuration Validity',
                    'status': 'pass',
                    'details': {
                        'system_config_loaded': bool(system_config),
                        'audio_config': 'audio' in system_config,
                        'network_config': 'network' in system_config
                    }
                }
            except Exception as e:
                config_test = {
                    'name': 'Configuration Validity',
                    'status': 'fail',
                    'error': str(e)
                }
            diagnostics['tests'].append(config_test)
        
        # Test 3: Network interfaces
        try:
            interfaces = get_network_interfaces()
            active_interfaces = sum(1 for iface in interfaces if iface.get('is_up', False))
            
            diagnostics['tests'].append({
                'name': 'Network Interfaces',
                'status': 'pass' if active_interfaces > 0 else 'fail',
                'details': {
                    'total_interfaces': len(interfaces),
                    'active_interfaces': active_interfaces,
                    'has_multicast_capable': any(iface.get('supports_multicast', False) for iface in interfaces)
                }
            })
        except Exception as e:
            diagnostics['tests'].append({
                'name': 'Network Interfaces',
                'status': 'fail',
                'error': str(e)
            })
        
        # Test 4: Resource availability
        try:
            memory = psutil.virtual_memory()
            memory_test = {
                'name': 'Resource Availability',
                'status': 'pass' if memory.percent < 90 else 'warning',
                'details': {
                    'memory_usage_percent': memory.percent,
                    'available_memory_gb': round(memory.available / (1024**3), 2)
                }
            }
            diagnostics['tests'].append(memory_test)
        except Exception as e:
            diagnostics['tests'].append({
                'name': 'Resource Availability',
                'status': 'fail',
                'error': str(e)
            })
        
        # Overall status
        test_statuses = [test['status'] for test in diagnostics['tests']]
        if 'fail' in test_statuses:
            overall_status = 'fail'
        elif 'warning' in test_statuses:
            overall_status = 'warning'
        else:
            overall_status = 'pass'
        
        diagnostics['overall_status'] = overall_status
        
        return jsonify({
            'success': True,
            'diagnostics': diagnostics
        })
        
    except Exception as e:
        logger.error(f"Error running diagnostics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_network_interfaces():
    """Get information about network interfaces"""
    try:
        interfaces = []
        
        # Get network interface information
        for interface_name, addresses in psutil.net_if_addrs().items():
            interface_stats = psutil.net_if_stats().get(interface_name)
            
            interface_info = {
                'name': interface_name,
                'is_up': interface_stats.isup if interface_stats else False,
                'mtu': interface_stats.mtu if interface_stats else 0,
                'speed': interface_stats.speed if interface_stats else 0,
                'addresses': []
            }
            
            for addr in addresses:
                if addr.family == socket.AF_INET:  # IPv4
                    interface_info['addresses'].append({
                        'type': 'IPv4',
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
                elif addr.family == socket.AF_INET6:  # IPv6
                    interface_info['addresses'].append({
                        'type': 'IPv6',
                        'address': addr.address,
                        'netmask': addr.netmask
                    })
            
            # Check if interface supports multicast
            interface_info['supports_multicast'] = check_multicast_support(interface_name)
            
            interfaces.append(interface_info)
        
        return interfaces
        
    except Exception as e:
        logger.error(f"Error getting network interfaces: {e}")
        return []

def check_multicast_support(interface_name):
    """Check if an interface supports multicast"""
    try:
        # This is a simplified check - in production, you might want more sophisticated detection
        return interface_name != 'lo' and not interface_name.startswith('docker')
    except Exception:
        return False

@status_bp.route('/logs', methods=['GET'])
def get_recent_logs():
    """Get recent log entries"""
    try:
        # This is a simplified implementation
        # In production, you would integrate with your logging system
        
        logs = {
            'timestamp': datetime.now().isoformat(),
            'entries': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'message': 'System status requested',
                    'component': 'status_api'
                }
            ],
            'total_entries': 1
        }
        
        return jsonify({
            'success': True,
            'logs': logs
        })
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
