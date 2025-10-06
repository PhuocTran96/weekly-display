#!/usr/bin/env python3
"""
History Routes - API endpoints for job history management
"""

from flask import Blueprint, jsonify, request, send_file
from app.services.job_storage import JobStorage
from app.services.processor import send_email_notifications
import os

# Create blueprint
history_bp = Blueprint('history', __name__)

# Initialize job storage
job_storage = JobStorage()


@history_bp.route('/', methods=['GET'])
def get_history():
    """
    Get job history with pagination and filtering

    Query params:
        - page: Page number (default: 1)
        - limit: Items per page (default: 20)
        - week: Filter by week number (optional)
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        week = request.args.get('week')

        if week:
            # Filter by week
            jobs = job_storage.get_jobs_by_week(int(week))
            result = {
                'success': True,
                'jobs': jobs,
                'pagination': {
                    'page': 1,
                    'limit': len(jobs),
                    'total': len(jobs),
                    'total_pages': 1
                }
            }
        else:
            # Get all jobs with pagination
            result = job_storage.get_all_jobs(page=page, limit=limit)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/<job_id>', methods=['GET'])
def get_job_details(job_id):
    """
    Get complete details for a specific job

    Args:
        job_id: Job identifier
    """
    try:
        job_data = job_storage.get_job_by_id(job_id)

        if job_data:
            return jsonify({
                'success': True,
                'job': job_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """
    Delete a job from history

    Args:
        job_id: Job identifier
    """
    try:
        success = job_storage.delete_job(job_id)

        if success:
            return jsonify({
                'success': True,
                'message': f'Job {job_id} deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete job'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/<job_id>/resend-emails', methods=['POST'])
def resend_emails(job_id):
    """
    Resend email notifications for a completed job

    Args:
        job_id: Job identifier

    JSON body (optional):
        - selected_recipients: List of email addresses to send to (if not provided, sends to all)
    """
    try:
        # Get job data
        job_data = job_storage.get_job_by_id(job_id)

        if not job_data:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

        # Check if job was successful
        if job_data.get('status') != 'completed':
            return jsonify({
                'success': False,
                'error': 'Can only resend emails for successfully completed jobs'
            }), 400

        # Get week number from job
        week_num = job_data.get('week_num')
        if not week_num:
            return jsonify({
                'success': False,
                'error': 'Week number not found in job data'
            }), 400

        # Get selected recipients from request body (if any)
        request_data = request.get_json() or {}
        selected_recipients = request_data.get('selected_recipients')

        # Resend email notifications
        if selected_recipients:
            # Import the selective send function
            from app.services.processor import send_selective_emails
            result = send_selective_emails(week_num, selected_recipients)
        else:
            # Send to all recipients
            result = send_email_notifications(week_num)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/cleanup', methods=['POST'])
def cleanup_old_jobs():
    """
    Delete jobs older than specified days

    JSON body:
        - days: Number of days to keep (default: 90)
    """
    try:
        data = request.get_json() or {}
        days = data.get('days', 90)

        deleted_count = job_storage.cleanup_old_jobs(days=days)

        return jsonify({
            'success': True,
            'message': f'Cleaned up {deleted_count} old jobs',
            'deleted_count': deleted_count
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get statistics about job history
    """
    try:
        all_jobs = job_storage.get_all_jobs(limit=1000)  # Get all jobs
        jobs = all_jobs.get('jobs', [])

        # Calculate stats
        total_jobs = len(jobs)
        successful_jobs = len([j for j in jobs if j.get('status') == 'completed'])
        failed_jobs = len([j for j in jobs if j.get('status') == 'failed'])

        # Get unique weeks
        weeks = set(j.get('week_num') for j in jobs if j.get('week_num'))

        return jsonify({
            'success': True,
            'stats': {
                'total_jobs': total_jobs,
                'successful_jobs': successful_jobs,
                'failed_jobs': failed_jobs,
                'weeks_processed': len(weeks),
                'recent_jobs': jobs[:5]  # Last 5 jobs
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/<job_id>/download/<file_type>', methods=['GET'])
def download_file(job_id, file_type):
    """
    Download a file generated by a specific job

    Args:
        job_id: Job identifier
        file_type: Type of file to download (report, alert, increases, decreases)
    """
    try:
        # Get job data
        job_data = job_storage.get_job_by_id(job_id)

        if not job_data:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404

        # Get files from job data
        files = job_data.get('files', {})

        # Map file type to file path
        file_mapping = {
            'report': files.get('report_file'),
            'alert': files.get('alert_file'),
            'increases': files.get('increases_file'),
            'decreases': files.get('decreases_file')
        }

        filename = file_mapping.get(file_type)

        if not filename:
            return jsonify({
                'success': False,
                'error': f'File type "{file_type}" not found or not generated for this job'
            }), 404

        # Construct full file path
        file_path = os.path.join('reports', filename)

        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': f'File not found: {filename}. It may have been deleted.'
            }), 404

        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
