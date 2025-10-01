#!/usr/bin/env python3
"""
Filters Routes - API endpoints for alert filter management
"""

import json
import glob
from flask import Blueprint, jsonify, request
from app.services.filter_service import FilterService

# Create blueprint
filters_bp = Blueprint('filters', __name__)

# Initialize filter service
filter_service = FilterService()


def _get_alerts_data(week_num=None):
    """
    Helper function to get alerts data from JSON files

    Args:
        week_num: Optional week number to get specific week data

    Returns:
        List of alert dictionaries or None if no data found
    """
    try:
        # Determine which file to load
        if week_num:
            alert_file = f'reports/alerts-week-{week_num}.json'
        else:
            # Find the latest alerts file
            alert_files = glob.glob('reports/alerts-week-*.json')
            if not alert_files:
                return None
            alert_files.sort()  # Sort to get the latest
            alert_file = alert_files[-1]

        # Load and parse the JSON file
        with open(alert_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract alerts from the all_changes section which has complete data
        alerts = []
        for alert in data.get('all_changes', []):
            # Ensure we have all the required fields
            alert['change'] = alert.get('Difference', 0)
            alert['model'] = alert.get('Model', '')
            alert['channel'] = alert.get('Channel', '')
            alert['store'] = alert.get('Store_name', '')  # Use Store_name field
            alerts.append(alert)

        return alerts if alerts else None

    except Exception as e:
        print(f"Error loading alerts data: {e}")
        return None


@filters_bp.route('/', methods=['GET'])
def get_filters():
    """
    Get current filter configuration
    """
    try:
        filters = filter_service.load_filters()

        return jsonify({
            'success': True,
            'filters': filters
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@filters_bp.route('/', methods=['POST'])
def save_filters():
    """
    Save filter configuration

    JSON body:
        - min_threshold: Minimum change threshold
        - max_threshold: Maximum change threshold
        - whitelisted_models: List of allowed models
        - blacklisted_models: List of blocked models
        - channels: List of allowed channels
        - stores: List of allowed stores
        - enabled: Enable/disable filtering
    """
    try:
        filters = request.get_json()

        if not filters:
            return jsonify({
                'success': False,
                'error': 'No filter data provided'
            }), 400

        # Save filters
        success = filter_service.save_filters(filters)

        if success:
            # Return updated filters
            updated_filters = filter_service.load_filters()
            return jsonify({
                'success': True,
                'filters': updated_filters,
                'message': 'Filters saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save filters'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@filters_bp.route('/preview', methods=['POST'])
def preview_filters():
    """
    Preview filters on current data

    JSON body (optional):
        - filters: Custom filter configuration to test
        - week_num: Week number to get data for (default: latest)
    """
    try:
        data = request.get_json() or {}
        custom_filters = data.get('filters')
        week_num = data.get('week_num')

        # Get alerts from JSON file
        alerts = _get_alerts_data(week_num)

        if not alerts:
            return jsonify({
                'success': False,
                'error': 'No alert data available for preview'
            }), 404

        # Apply filters
        preview_result = filter_service.preview_filters(alerts, custom_filters)

        return jsonify({
            'success': True,
            'preview': preview_result,
            'total_alerts_available': len(alerts)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@filters_bp.route('/reset', methods=['POST'])
def reset_filters():
    """
    Reset filters to default values
    """
    try:
        # Get default filters
        default_filters = filter_service._default_filters.copy()

        # Save default filters
        success = filter_service.save_filters(default_filters)

        if success:
            return jsonify({
                'success': True,
                'filters': default_filters,
                'message': 'Filters reset to defaults'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to reset filters'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@filters_bp.route('/toggle', methods=['POST'])
def toggle_filters():
    """
    Toggle filter enabled/disabled status
    """
    try:
        data = request.get_json() or {}
        enabled = data.get('enabled')

        if enabled is None:
            return jsonify({
                'success': False,
                'error': 'Enabled status not provided'
            }), 400

        # Load current filters
        filters = filter_service.load_filters()

        # Update enabled status
        filters['enabled'] = bool(enabled)

        # Save updated filters
        success = filter_service.save_filters(filters)

        if success:
            updated_filters = filter_service.load_filters()
            return jsonify({
                'success': True,
                'filters': updated_filters,
                'message': f"Filters {'enabled' if enabled else 'disabled'}"
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to toggle filters'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@filters_bp.route('/models/search', methods=['GET'])
def search_models():
    """
    Search for available models in current data

    Query params:
        - week_num: Week number to search in (optional)
        - query: Search query (optional)
    """
    try:
        week_num = request.args.get('week_num', type=int)
        query = request.args.get('query', '').lower().strip()

        # Get alerts from JSON file
        alerts = _get_alerts_data(week_num)

        if not alerts:
            return jsonify({
                'success': True,
                'models': [],
                'message': 'No alert data available'
            })

        # Extract unique models
        models = set()
        for alert in alerts:
            model = alert.get('Model', '').strip()  # Note: 'Model' not 'model'
            if model:
                if not query or query in model.lower():
                    models.add(model)

        # Sort models alphabetically
        sorted_models = sorted(list(models))

        return jsonify({
            'success': True,
            'models': sorted_models,
            'total_count': len(sorted_models)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@filters_bp.route('/channels/list', methods=['GET'])
def list_channels():
    """
    Get list of available channels in current data
    """
    try:
        week_num = request.args.get('week_num', type=int)

        # Get alerts from JSON file
        alerts = _get_alerts_data(week_num)

        if not alerts:
            return jsonify({
                'success': True,
                'channels': [],
                'message': 'No alert data available'
            })

        # Extract unique channels from the actual Channel field
        channels = set()
        for alert in alerts:
            channel = alert.get('channel', '').strip()
            if channel:
                channels.add(channel)

        # Sort channels alphabetically
        sorted_channels = sorted(list(channels))

        return jsonify({
            'success': True,
            'channels': sorted_channels,
            'total_count': len(sorted_channels)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@filters_bp.route('/stores/list', methods=['GET'])
def list_stores():
    """
    Get list of available stores in current data
    """
    try:
        week_num = request.args.get('week_num', type=int)

        # Get alerts from JSON file
        alerts = _get_alerts_data(week_num)

        if not alerts:
            return jsonify({
                'success': True,
                'stores': [],
                'message': 'No alert data available'
            })

        # Extract unique stores from the actual Store field
        stores = set()
        for alert in alerts:
            store = alert.get('store', '').strip()
            if store:
                stores.add(store)

        # Sort stores alphabetically
        sorted_stores = sorted(list(stores))

        return jsonify({
            'success': True,
            'stores': sorted_stores,
            'total_count': len(sorted_stores)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500