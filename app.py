#!/usr/bin/env python3
"""
Flask Web Application for Weekly Display Tracking System
Provides web interface for CSV upload, processing, and report generation
"""

import os
import json
import uuid
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
import pandas as pd

# Import existing processing modules
try:
    from unified_scripts import DisplayTracker
except ImportError:
    from display_tracking_system import DisplayTracker

try:
    from chart_generator import ChartGenerator
except ImportError:
    # Fallback if chart_generator is not available
    ChartGenerator = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configuration
UPLOAD_FOLDER = 'uploads'
REPORTS_FOLDER = 'reports'
CHARTS_FOLDER = 'charts'
TEMPLATES_FOLDER = 'templates'
STATIC_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'csv'}

# Ensure directories exist
for folder in [UPLOAD_FOLDER, REPORTS_FOLDER, CHARTS_FOLDER, TEMPLATES_FOLDER, STATIC_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Job tracking for background processing
processing_jobs = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_files():
    """Remove files older than 24 hours"""
    cutoff_time = datetime.now() - timedelta(hours=24)

    for folder in [UPLOAD_FOLDER, REPORTS_FOLDER, CHARTS_FOLDER]:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_time:
                        try:
                            os.remove(file_path)
                            print(f"Cleaned up old file: {file_path}")
                        except Exception as e:
                            print(f"Error cleaning up {file_path}: {e}")

def process_data_background(job_id, raw_file_path, report_file_path, week_num):
    """Background processing function"""
    try:
        processing_jobs[job_id]['status'] = 'processing'
        processing_jobs[job_id]['progress'] = 10

        # Initialize DisplayTracker
        tracker = DisplayTracker()
        processing_jobs[job_id]['progress'] = 30

        # Process the data
        result = tracker.process_weekly_data(raw_file_path, report_file_path, week_num)
        processing_jobs[job_id]['progress'] = 70

        if result['success']:
            # Generate charts
            chart_generator = ChartGenerator()

            # Load alert data for charts
            alert_file = result.get('alert_file', f'alerts-week-{week_num}.json')
            if os.path.exists(alert_file):
                with open(alert_file, 'r', encoding='utf-8') as f:
                    alert_data = json.load(f)

                # Generate charts
                increases_data = None
                decreases_data = None

                if 'top_increases' in alert_data and alert_data['top_increases']:
                    increases_data = {
                        'Model': [item['Model'] for item in alert_data['top_increases']],
                        'Diff': [item['Difference'] for item in alert_data['top_increases']]
                    }

                if 'top_decreases' in alert_data and alert_data['top_decreases']:
                    decreases_data = {
                        'Model': [item['Model'] for item in alert_data['top_decreases']],
                        'Diff': [item['Difference'] for item in alert_data['top_decreases']]
                    }

                # Create charts and save to charts folder
                if increases_data:
                    chart_generator.create_increase_chart(
                        increases_data,
                        f"Top Model Display Increases W{week_num}",
                        f"week_{week_num}_increases"
                    )

                if decreases_data:
                    chart_generator.create_decrease_chart(
                        decreases_data,
                        f"Top Model Display Decreases W{week_num}",
                        f"week_{week_num}_decreases"
                    )

            processing_jobs[job_id]['progress'] = 100
            processing_jobs[job_id]['status'] = 'completed'
            processing_jobs[job_id]['result'] = {
                'success': True,
                'report_file': result['updated_report_file'],
                'alert_file': result['alert_file'],
                'summary': result['summary'],
                'charts': {
                    'increases': f"week_{week_num}_increases_chart.png",
                    'decreases': f"week_{week_num}_decreases_chart.png"
                }
            }
        else:
            processing_jobs[job_id]['status'] = 'failed'
            processing_jobs[job_id]['error'] = result['error']

    except Exception as e:
        processing_jobs[job_id]['status'] = 'failed'
        processing_jobs[job_id]['error'] = str(e)
        print(f"Processing error for job {job_id}: {e}")

@app.route('/')
def dashboard():
    """Main dashboard page"""
    cleanup_old_files()  # Clean up old files on each visit
    return render_template('dashboard.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """Handle file uploads"""
    if request.method == 'GET':
        return render_template('upload.html')

    try:
        # Check if files are present
        if 'raw_file' not in request.files or 'report_file' not in request.files:
            return jsonify({'error': 'Both raw data and previous report files are required'}), 400

        raw_file = request.files['raw_file']
        report_file = request.files['report_file']
        week_num = request.form.get('week_num', '40')

        # Validate files
        if raw_file.filename == '' or report_file.filename == '':
            return jsonify({'error': 'No files selected'}), 400

        if not (allowed_file(raw_file.filename) and allowed_file(report_file.filename)):
            return jsonify({'error': 'Only CSV files are allowed'}), 400

        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id

        # Save uploaded files
        raw_filename = secure_filename(f"{session_id}_raw_{raw_file.filename}")
        report_filename = secure_filename(f"{session_id}_report_{report_file.filename}")

        raw_file_path = os.path.join(UPLOAD_FOLDER, raw_filename)
        report_file_path = os.path.join(UPLOAD_FOLDER, report_filename)

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
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/process', methods=['POST'])
def process_data():
    """Start data processing"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        week_num = data.get('week_num', '40')

        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400

        # Find uploaded files
        raw_file_path = None
        report_file_path = None

        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.startswith(f"{session_id}_raw_"):
                raw_file_path = os.path.join(UPLOAD_FOLDER, filename)
            elif filename.startswith(f"{session_id}_report_"):
                report_file_path = os.path.join(UPLOAD_FOLDER, filename)

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
        thread = threading.Thread(
            target=process_data_background,
            args=(job_id, raw_file_path, report_file_path, int(week_num))
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'started'
        })

    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/status/<job_id>')
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

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated files"""
    try:
        # Check in reports folder first, then charts folder
        file_path = None

        if os.path.exists(os.path.join(REPORTS_FOLDER, filename)):
            file_path = os.path.join(REPORTS_FOLDER, filename)
        elif os.path.exists(os.path.join(CHARTS_FOLDER, filename)):
            file_path = os.path.join(CHARTS_FOLDER, filename)
        elif os.path.exists(filename):  # Check current directory for compatibility
            file_path = filename

        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/charts/<chart_type>/<filename>')
def serve_chart(chart_type, filename):
    """Serve chart images"""
    try:
        file_path = os.path.join(CHARTS_FOLDER, filename)

        if not os.path.exists(file_path):
            # Try without charts folder (for backward compatibility)
            if os.path.exists(filename):
                file_path = filename
            else:
                return jsonify({'error': 'Chart not found'}), 404

        return send_file(file_path)

    except Exception as e:
        return jsonify({'error': f'Chart serving failed: {str(e)}'}), 500

@app.route('/results/<job_id>')
def show_results(job_id):
    """Show processing results"""
    if job_id not in processing_jobs:
        flash('Processing job not found', 'error')
        return redirect(url_for('dashboard'))

    job = processing_jobs[job_id]

    if job['status'] != 'completed':
        flash('Processing not completed yet', 'warning')
        return redirect(url_for('dashboard'))

    return render_template('results.html',
                         job_id=job_id,
                         result=job['result'],
                         week_num=job['week_num'])

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413

@app.errorhandler(404)
def not_found(e):
    return render_template('dashboard.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("Starting Weekly Display Tracking Web Application...")
    print("Visit http://localhost:5000 to access the dashboard")

    # Create required directories
    for folder in [UPLOAD_FOLDER, REPORTS_FOLDER, CHARTS_FOLDER]:
        os.makedirs(folder, exist_ok=True)

    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)