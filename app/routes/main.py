#!/usr/bin/env python3
"""
Main routes - Dashboard and download endpoints
"""

from flask import Blueprint, render_template, send_file, jsonify, redirect, url_for, flash
import os

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def dashboard():
    """Main dashboard page"""
    from app.utils.file_utils import cleanup_old_files
    from flask import current_app

    cleanup_old_files([
        current_app.config['UPLOAD_FOLDER'],
        current_app.config['REPORTS_FOLDER'],
        current_app.config['CHARTS_FOLDER']
    ])
    return render_template('dashboard.html')


@main_bp.route('/download/<filename>')
def download_file(filename):
    """Download generated files"""
    from flask import current_app

    try:
        file_path = None
        folders = [
            current_app.config['REPORTS_FOLDER'],
            current_app.config['CHARTS_FOLDER']
        ]

        for folder in folders:
            potential_path = os.path.join(folder, filename)
            if os.path.exists(potential_path):
                file_path = potential_path
                break

        if os.path.exists(filename):
            file_path = filename

        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        current_app.logger.error(f'Download error: {e}')
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


@main_bp.route('/charts/<chart_type>/<filename>')
def serve_chart(chart_type, filename):
    """Serve chart images"""
    from flask import current_app

    try:
        file_path = os.path.join(current_app.config['CHARTS_FOLDER'], filename)

        if not os.path.exists(file_path):
            if os.path.exists(filename):
                file_path = filename
            else:
                return jsonify({'error': 'Chart not found'}), 404

        return send_file(file_path)

    except Exception as e:
        current_app.logger.error(f'Chart serving error: {e}')
        return jsonify({'error': f'Chart serving failed: {str(e)}'}), 500