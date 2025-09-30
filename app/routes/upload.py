#!/usr/bin/env python3
"""
Upload routes - File upload handling
"""

from flask import Blueprint, request, jsonify, render_template, session, current_app
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
import uuid
import pandas as pd

upload_bp = Blueprint('upload', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@upload_bp.route('/', methods=['GET', 'POST'])
def upload_files():
    """Handle file uploads"""
    if request.method == 'GET':
        return render_template('upload.html')

    try:
        # Validate file presence
        if 'raw_file' not in request.files or 'report_file' not in request.files:
            return jsonify({'error': 'Both raw data and previous report files are required'}), 400

        raw_file = request.files['raw_file']
        report_file = request.files['report_file']
        week_num = request.form.get('week_num', '40')

        # Validate filenames
        if raw_file.filename == '' or report_file.filename == '':
            return jsonify({'error': 'No files selected'}), 400

        if not (allowed_file(raw_file.filename) and allowed_file(report_file.filename)):
            return jsonify({'error': 'Only CSV files are allowed'}), 400

        # Generate session ID
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id

        # Save files
        upload_folder = current_app.config['UPLOAD_FOLDER']
        raw_filename = secure_filename(f"{session_id}_raw_{raw_file.filename}")
        report_filename = secure_filename(f"{session_id}_report_{report_file.filename}")

        raw_file_path = os.path.join(upload_folder, raw_filename)
        report_file_path = os.path.join(upload_folder, report_filename)

        raw_file.save(raw_file_path)
        report_file.save(report_file_path)

        # Validate CSV structure
        try:
            pd.read_csv(raw_file_path, nrows=5)
            pd.read_csv(report_file_path, nrows=5)
        except Exception as e:
            return jsonify({'error': f'Invalid CSV format: {str(e)}'}), 400

        return jsonify({
            'success': True,
            'session_id': session_id,
            'raw_file': raw_filename,
            'report_file': report_filename,
            'week_num': week_num
        })

    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413
    except Exception as e:
        current_app.logger.error(f'Upload error: {e}')
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500