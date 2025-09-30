#!/usr/bin/env python3
"""
Background data processing service
"""

import os
import json
import threading
from datetime import datetime


def start_background_processing(job_id, raw_file_path, report_file_path, week_num, processing_jobs):
    """Start background processing thread"""
    thread = threading.Thread(
        target=process_data_background,
        args=(job_id, raw_file_path, report_file_path, week_num, processing_jobs)
    )
    thread.daemon = True
    thread.start()


def process_data_background(job_id, raw_file_path, report_file_path, week_num, processing_jobs):
    """Background processing function - emails disabled by default"""
    try:
        processing_jobs[job_id]['status'] = 'processing'
        processing_jobs[job_id]['progress'] = 10
        processing_jobs[job_id]['week_num'] = week_num

        # Initialize DisplayTracker with email disabled
        try:
            from unified_scripts import DisplayTracker
        except ImportError:
            from display_tracking_system import DisplayTracker

        log_file_path = os.path.join('logs', 'display_tracker.log')
        tracker = DisplayTracker(
            log_file=log_file_path,
            enable_email=False,  # Always disable email during processing
            gmail_email='',
            gmail_password=''
        )
        processing_jobs[job_id]['progress'] = 30

        # Convert to absolute paths
        abs_raw_path = os.path.abspath(raw_file_path)
        abs_report_path = os.path.abspath(report_file_path)

        # Change to reports directory
        original_dir = os.getcwd()
        os.chdir('reports')

        try:
            # Process the data without sending emails
            result = tracker.process_weekly_data(
                raw_file=abs_raw_path,
                previous_report_file=abs_report_path,
                week_num=week_num,
                send_emails=False,  # Never send emails during processing
                boss_emails=[],
                send_pic_emails=False,
                send_boss_emails=False
            )
        finally:
            os.chdir(original_dir)

        processing_jobs[job_id]['progress'] = 70

        if result['success']:
            # Generate charts
            charts_created = generate_charts(result, week_num)
            processing_jobs[job_id]['progress'] = 100
            processing_jobs[job_id]['status'] = 'completed'
            processing_jobs[job_id]['result'] = {
                'success': True,
                'report_file': result['updated_report_file'],
                'alert_file': result['alert_file'],
                'increases_file': f'increases-week-{week_num}.csv',
                'decreases_file': f'decreases-week-{week_num}.csv',
                'summary': result['summary'],
                'charts': charts_created
            }
        else:
            processing_jobs[job_id]['status'] = 'failed'
            processing_jobs[job_id]['error'] = result['error']

    except Exception as e:
        processing_jobs[job_id]['status'] = 'failed'
        processing_jobs[job_id]['error'] = str(e)
        print(f"Processing error for job {job_id}: {e}")


def generate_charts(result, week_num):
    """Generate charts from processing results"""
    charts_created = {'increases': None, 'decreases': None}

    try:
        from chart_generator import ChartGenerator

        chart_generator = ChartGenerator()
        alert_file = os.path.join('reports', result.get('alert_file', f'alerts-week-{week_num}.json'))

        if os.path.exists(alert_file):
            with open(alert_file, 'r', encoding='utf-8') as f:
                alert_data = json.load(f)

            # Generate increases chart
            if 'top_increases' in alert_data and alert_data['top_increases']:
                increases_data = {
                    'Model': [item['Model'] for item in alert_data['top_increases']],
                    'Diff': [item['Difference'] for item in alert_data['top_increases']]
                }
                try:
                    chart_generator.create_increase_chart(
                        increases_data,
                        f"Top Model Display Increases W{week_num}",
                        f"week_{week_num}_increases"
                    )
                    increases_chart_file = f"week_{week_num}_increases_chart.png"
                    if os.path.exists(os.path.join('charts', increases_chart_file)):
                        charts_created['increases'] = increases_chart_file
                        print(f"Created increases chart: {increases_chart_file}")
                except Exception as e:
                    print(f"Failed to create increases chart: {e}")

            # Generate decreases chart
            if 'top_decreases' in alert_data and alert_data['top_decreases']:
                decreases_data = {
                    'Model': [item['Model'] for item in alert_data['top_decreases']],
                    'Diff': [item['Difference'] for item in alert_data['top_decreases']]
                }
                try:
                    chart_generator.create_decrease_chart(
                        decreases_data,
                        f"Top Model Display Decreases W{week_num}",
                        f"week_{week_num}_decreases"
                    )
                    decreases_chart_file = f"week_{week_num}_decreases_chart.png"
                    if os.path.exists(os.path.join('charts', decreases_chart_file)):
                        charts_created['decreases'] = decreases_chart_file
                        print(f"Created decreases chart: {decreases_chart_file}")
                except Exception as e:
                    print(f"Failed to create decreases chart: {e}")

    except Exception as e:
        print(f"Warning: Could not generate charts: {e}")

    return charts_created


def send_email_notifications(week_num):
    """Send email notifications for a completed processing job

    Args:
        week_num: Week number for the report

    Returns:
        dict: Result of email sending operation
    """
    try:
        # Get email configuration
        email_enabled = os.environ.get('EMAIL_ENABLED', 'False').lower() == 'true'

        if not email_enabled:
            return {
                'success': False,
                'error': 'Email notifications are not enabled. Please set EMAIL_ENABLED=True in .env'
            }

        gmail_email = os.environ.get('GMAIL_EMAIL', '')
        gmail_password = os.environ.get('GMAIL_APP_PASSWORD', '')
        boss_emails = os.environ.get('BOSS_EMAILS', '').split(',') if os.environ.get('BOSS_EMAILS') else []
        send_pic_emails = os.environ.get('SEND_PIC_EMAILS', 'True').lower() == 'true'
        send_boss_emails = os.environ.get('SEND_BOSS_EMAILS', 'True').lower() == 'true'

        if not gmail_email or not gmail_password:
            return {
                'success': False,
                'error': 'Email credentials not configured. Please set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env'
            }

        # Initialize email notifier
        try:
            from email_notifier import EmailNotifier
        except ImportError:
            return {
                'success': False,
                'error': 'Email notifier module not found'
            }

        notifier = EmailNotifier(gmail_email, gmail_password)

        # Load alert data
        alert_file = os.path.join('reports', f'alerts-week-{week_num}.json')
        if not os.path.exists(alert_file):
            return {
                'success': False,
                'error': f'Alert file not found: {alert_file}. Please process data first.'
            }

        with open(alert_file, 'r', encoding='utf-8') as f:
            alert_data = json.load(f)

        # Send emails
        emails_sent = 0
        errors = []

        # Send to PICs
        if send_pic_emails and 'pic_emails' in alert_data:
            for email_info in alert_data.get('pic_emails', []):
                try:
                    notifier.send_pic_notification(
                        email_info['email'],
                        email_info['store_name'],
                        email_info['changes']
                    )
                    emails_sent += 1
                except Exception as e:
                    error_msg = f"Failed to send email to {email_info.get('email', 'unknown')}: {e}"
                    print(error_msg)
                    errors.append(error_msg)

        # Send to bosses
        if send_boss_emails and boss_emails:
            try:
                notifier.send_boss_summary(
                    boss_emails,
                    alert_data.get('summary', {}),
                    alert_data.get('top_increases', []),
                    alert_data.get('top_decreases', [])
                )
                emails_sent += len(boss_emails)
            except Exception as e:
                error_msg = f"Failed to send boss emails: {e}"
                print(error_msg)
                errors.append(error_msg)

        if emails_sent > 0:
            return {
                'success': True,
                'emails_sent': emails_sent,
                'message': f'Successfully sent {emails_sent} email notification(s)',
                'errors': errors if errors else None
            }
        else:
            return {
                'success': False,
                'error': 'No emails were sent. ' + '; '.join(errors) if errors else 'No recipients found'
            }

    except Exception as e:
        return {
            'success': False,
            'error': f'Email sending failed: {str(e)}'
        }