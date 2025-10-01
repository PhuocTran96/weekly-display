#!/usr/bin/env python3
"""
Email Service - Handles email preview and selective sending
"""

import os
import json
import logging
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime


class EmailService:
    """
    Service for email preview and selective email sending
    """

    def __init__(self):
        """Initialize Email Service"""
        self.logger = logging.getLogger(__name__)

    def get_email_preview(self, week_num: int) -> Dict:
        """
        Get email preview data for a given week

        Args:
            week_num: Week number

        Returns:
            Dict containing recipients, subject, body preview, and metadata
        """
        try:
            # Load alert data
            alert_file = os.path.join('reports', f'alerts-week-{week_num}.json')

            if not os.path.exists(alert_file):
                return {
                    'success': False,
                    'error': f'Alert file not found for week {week_num}. Please process data first.'
                }

            with open(alert_file, 'r', encoding='utf-8') as f:
                alert_data = json.load(f)

            # Extract recipients
            recipients = self._extract_recipients(alert_data, week_num)

            # Generate email previews
            pic_preview = None
            boss_preview = None

            if recipients['pics']:
                # Generate sample PIC email preview (using first PIC as example)
                first_pic = recipients['pics'][0]
                pic_preview = self._generate_pic_preview(first_pic, week_num)

            if recipients['bosses']:
                boss_preview = self._generate_boss_preview(alert_data, week_num)

            total_recipients = len(recipients['pics']) + len(recipients['bosses'])

            # Add helpful message if no recipients found
            message = None
            if total_recipients == 0:
                if 'pic_decreases' not in alert_data:
                    message = 'This alert file was generated with an older version. Please reprocess your data to generate proper email recipients, or configure BOSS_EMAILS in your .env file to enable boss notifications.'
                else:
                    message = 'No email recipients found. Please configure BOSS_EMAILS in your .env file or ensure PIC contact information is available.'

            return {
                'success': True,
                'week_num': week_num,
                'recipients': recipients,
                'pic_preview': pic_preview,
                'boss_preview': boss_preview,
                'summary': alert_data.get('summary', {}),
                'total_recipients': total_recipients,
                'message': message
            }

        except Exception as e:
            self.logger.error(f"Error getting email preview: {e}")
            return {
                'success': False,
                'error': f'Failed to generate email preview: {str(e)}'
            }

    def send_selective_emails(self, week_num: int, selected_recipient_ids: List[str]) -> Dict:
        """
        Send emails to selected recipients only

        Args:
            week_num: Week number
            selected_recipient_ids: List of recipient IDs to send to (format: "pic_{email}" or "boss_{email}")

        Returns:
            Dict with success status and results per recipient
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

            if not gmail_email or not gmail_password:
                return {
                    'success': False,
                    'error': 'Email credentials not configured'
                }

            # Initialize email notifier
            from email_notifier import EmailNotifier
            notifier = EmailNotifier(gmail_email, gmail_password)

            # Load alert data
            alert_file = os.path.join('reports', f'alerts-week-{week_num}.json')

            if not os.path.exists(alert_file):
                return {
                    'success': False,
                    'error': f'Alert file not found for week {week_num}'
                }

            with open(alert_file, 'r', encoding='utf-8') as f:
                alert_data = json.load(f)

            # Send emails to selected recipients
            results = []
            emails_sent = 0
            errors = []

            for recipient_id in selected_recipient_ids:
                try:
                    recipient_type, recipient_email = recipient_id.split('_', 1)

                    if recipient_type == 'pic':
                        # Send PIC email
                        success = self._send_pic_email(
                            notifier,
                            alert_data,
                            recipient_email,
                            week_num
                        )

                        if success:
                            emails_sent += 1
                            results.append({
                                'recipient': recipient_email,
                                'type': 'PIC',
                                'status': 'sent'
                            })
                        else:
                            errors.append(f"Failed to send to PIC: {recipient_email}")
                            results.append({
                                'recipient': recipient_email,
                                'type': 'PIC',
                                'status': 'failed'
                            })

                    elif recipient_type == 'boss':
                        # Send boss email
                        success = self._send_boss_email(
                            notifier,
                            alert_data,
                            recipient_email,
                            week_num
                        )

                        if success:
                            emails_sent += 1
                            results.append({
                                'recipient': recipient_email,
                                'type': 'Boss',
                                'status': 'sent'
                            })
                        else:
                            errors.append(f"Failed to send to Boss: {recipient_email}")
                            results.append({
                                'recipient': recipient_email,
                                'type': 'Boss',
                                'status': 'failed'
                            })

                except Exception as e:
                    error_msg = f"Failed to send to {recipient_id}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                    results.append({
                        'recipient': recipient_id,
                        'type': 'Unknown',
                        'status': 'failed',
                        'error': str(e)
                    })

            return {
                'success': emails_sent > 0,
                'emails_sent': emails_sent,
                'total_selected': len(selected_recipient_ids),
                'results': results,
                'errors': errors if errors else None,
                'message': f'Successfully sent {emails_sent} out of {len(selected_recipient_ids)} email(s)'
            }

        except Exception as e:
            self.logger.error(f"Error sending selective emails: {e}")
            return {
                'success': False,
                'error': f'Failed to send emails: {str(e)}'
            }

    def _extract_recipients(self, alert_data: Dict, week_num: int) -> Dict:
        """Extract and format recipient list from alert data"""
        recipients = {
            'pics': [],
            'bosses': []
        }

        # Extract PICs from decreases data (NEW FORMAT)
        if 'pic_decreases' in alert_data:
            for pic_email, pic_data in alert_data['pic_decreases'].items():
                stores_info = []
                decrease_count = 0

                for store_data in pic_data.get('stores', []):
                    stores_info.append(store_data['store_info']['Store_name'])
                    decrease_count += len(store_data.get('decreases', []))

                recipients['pics'].append({
                    'id': f'pic_{pic_email}',
                    'email': pic_email,
                    'name': pic_data.get('pic_name', 'Unknown'),
                    'type': 'PIC',
                    'stores': stores_info,
                    'decrease_count': decrease_count,
                    'store_count': len(pic_data.get('stores', []))
                })

        # Fallback: Handle OLD FORMAT (no pic_decreases, just top_decreases)
        elif 'top_decreases' in alert_data and alert_data['top_decreases']:
            # Show a note that recipients need to be configured
            self.logger.warning(f"Alert file for week {week_num} uses old format without PIC information")

        # Extract Boss emails from environment or alert data
        boss_emails = os.environ.get('BOSS_EMAILS', '').split(',')
        boss_emails = [email.strip() for email in boss_emails if email.strip()]

        # Handle summary from new format or create from old format
        if boss_emails:
            if 'summary' in alert_data:
                # NEW FORMAT: Use existing summary
                summary = alert_data['summary']
            else:
                # OLD FORMAT: Create summary from available data
                summary = {
                    'stores_affected': 0,  # Unknown in old format
                    'total_decreases': alert_data.get('models_decreased', 0),
                    'models_decreased': alert_data.get('models_decreased', 0)
                }

            for boss_email in boss_emails:
                recipients['bosses'].append({
                    'id': f'boss_{boss_email}',
                    'email': boss_email,
                    'name': 'Management',
                    'type': 'Boss',
                    'stores_affected': summary.get('stores_affected', 0),
                    'total_decreases': summary.get('total_decreases', 0),
                    'models_decreased': summary.get('models_decreased', 0)
                })

        return recipients

    def _generate_pic_preview(self, pic_recipient: Dict, week_num: int) -> Dict:
        """Generate PIC email preview"""
        store_names = ', '.join(pic_recipient['stores'][:3])
        if pic_recipient['store_count'] > 3:
            store_names += f" and {pic_recipient['store_count'] - 3} more"

        subject = f"⚠️ Display Decrease Alert - {store_names} - Week {week_num}"

        preview_body = f"""
        <p>Dear {pic_recipient['name']},</p>
        <p>This is an automated notification regarding display decreases detected at your store(s).</p>
        <p><strong>Stores Affected:</strong> {pic_recipient['store_count']}</p>
        <p><strong>Total Decreases:</strong> {pic_recipient['decrease_count']}</p>
        <p>Please review the display decreases and take appropriate action.</p>
        """

        return {
            'subject': subject,
            'body_html': preview_body,
            'recipient': pic_recipient
        }

    def _generate_boss_preview(self, alert_data: Dict, week_num: int) -> Dict:
        """Generate Boss email preview"""
        summary = alert_data.get('summary', {})

        subject = f"📊 Weekly Display Decrease Summary - Week {week_num}"

        preview_body = f"""
        <p>Dear Management,</p>
        <p>This is your weekly summary of display decreases across all monitored stores.</p>
        <h3>Summary Statistics</h3>
        <ul>
            <li><strong>Stores Affected:</strong> {summary.get('stores_affected', 0)}</li>
            <li><strong>Models Decreased:</strong> {summary.get('models_decreased', 0)}</li>
            <li><strong>Total Decrease:</strong> {summary.get('total_decreases', 0)}</li>
        </ul>
        <p>Detailed decrease report is attached to this email.</p>
        """

        return {
            'subject': subject,
            'body_html': preview_body,
            'summary': summary
        }

    def _send_pic_email(self, notifier, alert_data: Dict, pic_email: str, week_num: int) -> bool:
        """Send email to a specific PIC"""
        try:
            if 'pic_decreases' not in alert_data or pic_email not in alert_data['pic_decreases']:
                self.logger.warning(f"No decrease data found for PIC: {pic_email}")
                return False

            pic_data = alert_data['pic_decreases'][pic_email]
            stores_data = pic_data.get('stores', [])
            pic_name = pic_data.get('pic_name', 'Unknown')

            if not stores_data:
                self.logger.warning(f"No stores data for PIC: {pic_email}")
                return False

            # Send email using EmailNotifier
            success = notifier.send_decrease_alert_to_pic(
                pic_email=pic_email,
                pic_name=pic_name,
                stores_data=stores_data,
                week_num=week_num
            )

            return success

        except Exception as e:
            self.logger.error(f"Error sending PIC email to {pic_email}: {e}")
            return False

    def _send_boss_email(self, notifier, alert_data: Dict, boss_email: str, week_num: int) -> bool:
        """Send email to a specific boss"""
        try:
            summary = alert_data.get('summary', {})

            # Load decreases CSV
            decreases_file = os.path.join('reports', f'decreases-week-{week_num}.csv')
            csv_attachment = None

            if os.path.exists(decreases_file):
                csv_attachment = decreases_file
                decreases_df = pd.read_csv(decreases_file, encoding='utf-8')
            else:
                # Create empty dataframe if file doesn't exist
                decreases_df = pd.DataFrame()

            # Send email using EmailNotifier
            success = notifier.send_boss_summary(
                boss_emails=[boss_email],
                summary_data=summary,
                decreases_df=decreases_df,
                week_num=week_num,
                csv_attachment_path=csv_attachment
            )

            return success

        except Exception as e:
            self.logger.error(f"Error sending boss email to {boss_email}: {e}")
            return False
