#!/usr/bin/env python3
"""
Main routes - Dashboard and download endpoints
"""

from flask import Blueprint, render_template, send_file, send_from_directory, jsonify, redirect, url_for, flash
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


@main_bp.route('/history')
def history():
    """Processing history page"""
    return render_template('history.html')


@main_bp.route('/filters')
def filters():
    """Alert filters configuration page"""
    return render_template('filters.html')


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
        # Get absolute path to charts directory
        charts_folder = current_app.config['CHARTS_FOLDER']

        # If relative path, make it absolute from project root
        if not os.path.isabs(charts_folder):
            # Get project root (parent directory of app folder)
            project_root = os.path.dirname(current_app.root_path)
            charts_folder = os.path.join(project_root, charts_folder)

        # Check if file exists
        file_path = os.path.join(charts_folder, filename)
        if not os.path.exists(file_path):
            current_app.logger.error(f'Chart file not found: {file_path}')
            return jsonify({'error': f'Chart not found: {filename}'}), 404

        # Use send_from_directory for better security and path handling
        return send_from_directory(charts_folder, filename)

    except Exception as e:
        current_app.logger.error(f'Chart serving error: {e}')
        return jsonify({'error': f'Chart serving failed: {str(e)}'}), 500