#!/usr/bin/env python3
"""
Process routes - Data processing endpoints
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
import os
import uuid
from datetime import datetime

process_bp = Blueprint('process', __name__)

# Global job tracking
processing_jobs = {}


@process_bp.route('/', methods=['POST'])
def start_processing():
    """Start data processing"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        week_num = data.get('week_num', '40')

        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400

        # Find uploaded files
        upload_folder = current_app.config['UPLOAD_FOLDER']
        raw_file_path = None
        report_file_path = None

        for filename in os.listdir(upload_folder):
            if filename.startswith(f"{session_id}_raw_"):
                raw_file_path = os.path.join(upload_folder, filename)
            elif filename.startswith(f"{session_id}_report_"):
                report_file_path = os.path.join(upload_folder, filename)

        if not raw_file_path or not report_file_path:
            return jsonify({'error': 'Uploaded files not found'}), 404

        # Create processing job
        job_id = str(uuid.uuid4())
        processing_jobs[job_id] = {
            'status': 'started',
            'progress': 0,
            'session_id': session_id,
            'week_num': week_num,
            'started_at': datetime.now().isoformat()
        }

        # Start background processing
        from app.services.processor import start_background_processing
        start_background_processing(job_id, raw_file_path, report_file_path, int(week_num), processing_jobs)

        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'started'
        })

    except Exception as e:
        current_app.logger.error(f'Processing start error: {e}')
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


@process_bp.route('/status/<job_id>')
def get_status(job_id):
    """Get processing status"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = processing_jobs[job_id]
    response_data = {
        'job_id': job_id,
        'status': job['status'],
        'progress': job.get('progress', 0)
    }

    if job['status'] == 'completed':
        response_data['result'] = job['result']
    elif job['status'] == 'failed':
        response_data['error'] = job.get('error', 'Unknown error')

    return jsonify(response_data)


@process_bp.route('/results/<job_id>')
def show_results(job_id):
    """Show processing results"""
    if job_id not in processing_jobs:
        flash('Processing job not found', 'error')
        return redirect(url_for('main.dashboard'))

    job = processing_jobs[job_id]

    if job['status'] != 'completed':
        flash('Processing not completed yet', 'warning')
        return redirect(url_for('main.dashboard'))

    return render_template('results.html',
                         job_id=job_id,
                         result=job['result'],
                         week_num=job['week_num'])


@process_bp.route('/send-emails', methods=['POST'])
def send_emails():
    """Send email notifications for processed data"""
    try:
        data = request.get_json()
        week_num = data.get('week_num')

        if not week_num:
            return jsonify({'error': 'Week number is required'}), 400

        # Import and call email sending function
        from app.services.processor import send_email_notifications

        result = send_email_notifications(int(week_num))

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        current_app.logger.error(f'Email sending error: {e}')
        return jsonify({
            'success': False,
            'error': f'Failed to send emails: {str(e)}'
        }), 500


@process_bp.route('/preview-email', methods=['POST'])
def preview_email():
    """Get email preview before sending"""
    try:
        data = request.get_json()
        week_num = data.get('week_num')

        if not week_num:
            return jsonify({'error': 'Week number is required'}), 400

        # Import email service
        from app.services.email_service import EmailService

        email_service = EmailService()
        result = email_service.get_email_preview(int(week_num))

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        current_app.logger.error(f'Email preview error: {e}')
        return jsonify({
            'success': False,
            'error': f'Failed to generate email preview: {str(e)}'
        }), 500


@process_bp.route('/send-selective-emails', methods=['POST'])
def send_selective_emails():
    """Send emails to selected recipients only"""
    try:
        data = request.get_json()
        week_num = data.get('week_num')
        selected_recipients = data.get('selected_recipients', [])

        if not week_num:
            return jsonify({'error': 'Week number is required'}), 400

        if not selected_recipients:
            return jsonify({'error': 'No recipients selected'}), 400

        # Import email service
        from app.services.email_service import EmailService

        email_service = EmailService()
        result = email_service.send_selective_emails(int(week_num), selected_recipients)

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        current_app.logger.error(f'Selective email sending error: {e}')
        return jsonify({
            'success': False,
            'error': f'Failed to send selective emails: {str(e)}'
        }), 500