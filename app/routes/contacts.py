#!/usr/bin/env python3
"""
Contacts API routes - Contact management endpoints
"""

from flask import Blueprint, request, jsonify, render_template, Response, current_app
from io import StringIO
import pandas as pd

contacts_bp = Blueprint('contacts', __name__)


@contacts_bp.route('/')
def contacts_page():
    """Contacts management page"""
    return render_template('contacts.html')


@contacts_bp.route('/all', methods=['GET'])
def get_contacts():
    """Get all contacts"""
    try:
        from db_manager import DatabaseManager

        db = DatabaseManager()
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        contacts = db.get_all_contacts(active_only=active_only)
        db.close()

        return jsonify({
            'success': True,
            'contacts': contacts,
            'count': len(contacts)
        })
    except Exception as e:
        current_app.logger.error(f'Get contacts error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@contacts_bp.route('/<elux_id>', methods=['GET'])
def get_contact(elux_id):
    """Get single contact by Elux ID"""
    try:
        from db_manager import DatabaseManager

        current_app.logger.info(f'Getting contact for Elux ID: {elux_id} (type: {type(elux_id)})')

        db = DatabaseManager()
        contact = db.get_contact_by_elux_id(elux_id)
        db.close()

        current_app.logger.info(f'Contact found: {contact is not None}')
        if contact:
            current_app.logger.info(f'Contact data: {contact}')

        if contact:
            return jsonify({'success': True, 'contact': contact})
        else:
            current_app.logger.warning(f'Contact not found for Elux ID: {elux_id}')
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
    except Exception as e:
        current_app.logger.error(f'Get contact error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@contacts_bp.route('/add', methods=['POST'])
def add_contact():
    """Add new contact"""
    try:
        from db_manager import DatabaseManager

        data = request.get_json()

        # Validate required fields
        required_fields = ['elux_id', 'dealer_id', 'store_name', 'channel', 'pic_name', 'pic_email']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        db = DatabaseManager()
        result = db.add_contact(data)
        db.close()

        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        current_app.logger.error(f'Add contact error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@contacts_bp.route('/<elux_id>', methods=['PUT'])
def update_contact(elux_id):
    """Update existing contact"""
    try:
        from db_manager import DatabaseManager

        data = request.get_json()
        current_app.logger.info(f'Updating contact {elux_id} with data: {data}')

        db = DatabaseManager()
        result = db.update_contact(elux_id, data)
        db.close()

        current_app.logger.info(f'Update result: {result}')

        if result['success']:
            return jsonify(result)
        else:
            status_code = 404 if 'not found' in result.get('error', '').lower() else 400
            return jsonify(result), status_code
    except Exception as e:
        current_app.logger.error(f'Update contact error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@contacts_bp.route('/<elux_id>', methods=['DELETE'])
def delete_contact(elux_id):
    """Delete contact (soft delete by default)"""
    try:
        from db_manager import DatabaseManager

        soft_delete = request.args.get('soft', 'true').lower() == 'true'
        db = DatabaseManager()
        result = db.delete_contact(elux_id, soft_delete=soft_delete)
        db.close()

        return jsonify(result), 200 if result['success'] else 404
    except Exception as e:
        current_app.logger.error(f'Delete contact error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@contacts_bp.route('/search', methods=['GET'])
def search_contacts():
    """Search contacts"""
    try:
        from db_manager import DatabaseManager

        search_term = request.args.get('q', '')
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        if not search_term:
            return jsonify({'success': False, 'error': 'Search term required'}), 400

        db = DatabaseManager()
        results = db.search_contacts(search_term, active_only=active_only)
        db.close()

        return jsonify({
            'success': True,
            'contacts': results,
            'count': len(results)
        })
    except Exception as e:
        current_app.logger.error(f'Search contacts error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@contacts_bp.route('/export', methods=['GET'])
def export_contacts():
    """Export contacts to CSV"""
    try:
        from db_manager import DatabaseManager

        db = DatabaseManager()
        df = db.get_contacts_dataframe(active_only=False)
        db.close()

        if df.empty:
            return jsonify({'success': False, 'error': 'No contacts to export'}), 404

        output = StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=contacts_export.csv'}
        )
    except Exception as e:
        current_app.logger.error(f'Export contacts error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@contacts_bp.route('/import', methods=['POST'])
def import_contacts():
    """Import contacts from CSV"""
    try:
        from db_manager import DatabaseManager

        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Only CSV files allowed'}), 400

        df = pd.read_csv(file)
        contacts_list = df.to_dict('records')

        db = DatabaseManager()
        result = db.bulk_import_contacts(contacts_list)
        db.close()

        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f'Import contacts error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500