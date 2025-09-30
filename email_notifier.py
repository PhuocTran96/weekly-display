#!/usr/bin/env python3
"""
Email Notification Module for Display Tracking System
Handles Gmail SMTP email sending for decrease alerts
"""

import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmailNotifier:
    """
    Gmail SMTP email notifier for display decrease alerts
    """

    def __init__(self, smtp_email=None, smtp_password=None, enabled=True):
        """
        Initialize Email Notifier

        Args:
            smtp_email: Gmail address for sending
            smtp_password: Gmail App Password
            enabled: Whether email notifications are enabled
        """
        self.smtp_email = smtp_email or os.environ.get('GMAIL_EMAIL')
        self.smtp_password = smtp_password or os.environ.get('GMAIL_APP_PASSWORD')
        self.enabled = enabled and self.smtp_email and self.smtp_password

        # Gmail SMTP settings
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587  # TLS

        # Setup logging
        self.logger = logging.getLogger(__name__)

        if not self.enabled:
            self.logger.warning("Email notifications disabled - missing credentials or explicitly disabled")

    def send_decrease_alert_to_pic(self, pic_email: str, pic_name: str,
                                    stores_data: List[Dict], week_num: int) -> bool:
        """
        Send decrease alert email to shop PIC (supports multiple stores)

        Args:
            pic_email: PIC's email address
            pic_name: PIC's name
            stores_data: List of store dicts, each containing:
                         - store_info: Dict with Elux_ID, Dealer_ID, Store_name, Channel
                         - decreases: List of decrease records for that store
            week_num: Week number

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            self.logger.info(f"Email notifications disabled - would have sent to {pic_email}")
            return False

        try:
            # Determine subject based on number of stores
            if len(stores_data) == 1:
                subject = f"⚠️ Display Decrease Alert - {stores_data[0]['store_info']['Store_name']} - Week {week_num}"
            else:
                subject = f"⚠️ Display Decrease Alert - {len(stores_data)} Stores - Week {week_num}"

            # Create email
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_email
            msg['To'] = pic_email
            msg['Subject'] = subject

            # Create HTML and plain text versions
            html_content = self._generate_pic_email_html(pic_name, stores_data, week_num)
            text_content = self._generate_pic_email_text(pic_name, stores_data, week_num)

            # Attach both versions
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            self._send_email(msg, [pic_email])

            store_names = [s['store_info']['Store_name'] for s in stores_data]
            self.logger.info(f"Decrease alert sent to {pic_email} for {len(stores_data)} store(s): {', '.join(store_names)}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email to {pic_email}: {e}")
            return False

    def send_boss_summary(self, boss_emails: List[str], summary_data: Dict,
                         decreases_df: pd.DataFrame, week_num: int,
                         csv_attachment_path: Optional[str] = None) -> bool:
        """
        Send summary email to boss with all decreases

        Args:
            boss_emails: List of boss email addresses
            summary_data: Summary statistics
            decreases_df: DataFrame with all decreases
            week_num: Week number
            csv_attachment_path: Optional path to CSV file to attach

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            self.logger.info(f"Email notifications disabled - would have sent to {boss_emails}")
            return False

        try:
            # Create email
            msg = MIMEMultipart('mixed')
            msg['From'] = self.smtp_email
            msg['To'] = ', '.join(boss_emails)
            msg['Subject'] = f"📊 Weekly Display Decrease Summary - Week {week_num}"

            # Create HTML and plain text versions
            html_content = self._generate_boss_email_html(summary_data, decreases_df, week_num)
            text_content = self._generate_boss_email_text(summary_data, decreases_df, week_num)

            # Attach text versions
            msg_alt = MIMEMultipart('alternative')
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg_alt.attach(part1)
            msg_alt.attach(part2)
            msg.attach(msg_alt)

            # Attach CSV file if provided
            if csv_attachment_path and os.path.exists(csv_attachment_path):
                with open(csv_attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition',
                                  f'attachment; filename="{os.path.basename(csv_attachment_path)}"')
                    msg.attach(part)

            # Send email
            self._send_email(msg, boss_emails)

            self.logger.info(f"Boss summary sent to {', '.join(boss_emails)}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send boss summary: {e}")
            return False

    def send_test_email(self, recipient_email: str) -> bool:
        """
        Send a test email to verify configuration

        Args:
            recipient_email: Email address to send test to

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            msg = MIMEText('This is a test email from the Display Tracking System. Email notifications are working correctly!')
            msg['From'] = self.smtp_email
            msg['To'] = recipient_email
            msg['Subject'] = 'Test Email - Display Tracking System'

            self._send_email(msg, [recipient_email])
            self.logger.info(f"Test email sent to {recipient_email}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send test email: {e}")
            return False

    def _send_email(self, msg: MIMEMultipart, recipients: List[str]):
        """
        Internal method to send email via Gmail SMTP

        Args:
            msg: Email message object
            recipients: List of recipient email addresses
        """
        try:
            # Connect to Gmail SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable TLS encryption

            # Login
            server.login(self.smtp_email, self.smtp_password)

            # Send email
            server.send_message(msg)

            # Close connection
            server.quit()

        except smtplib.SMTPAuthenticationError:
            self.logger.error("SMTP Authentication failed - check Gmail email and App Password")
            raise
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error occurred: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error sending email: {e}")
            raise

    def _generate_pic_email_html(self, pic_name: str, stores_data: List[Dict],
                                  week_num: int) -> str:
        """Generate HTML email content for PIC (supports multiple stores)"""

        # Build store blocks HTML
        stores_html = ""
        for idx, store_data in enumerate(stores_data):
            store_info = store_data['store_info']
            decreases = store_data['decreases']

            # Build decreases table for this store
            rows_html = ""
            for dec in decreases:
                rows_html += f"""
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">{dec['Model']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{int(dec['Previous'])}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">{int(dec['Current'])}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; text-align: center; color: #dc3545; font-weight: bold;">{int(dec['Difference'])}</td>
                </tr>
                """

            # Add separator between stores (except before first store)
            separator = '<hr style="border: none; border-top: 2px solid #dee2e6; margin: 30px 0;">' if idx > 0 else ''

            stores_html += f"""
                {separator}
                <div class="store-block">
                    <div class="store-info">
                        <h3 style="margin-top: 0;">Store {idx + 1}: {store_info['Store_name']}</h3>
                        <p><strong>Elux ID:</strong> {store_info['Elux_ID']}</p>
                        <p><strong>Dealer ID:</strong> {store_info['Dealer_ID']}</p>
                        <p><strong>Channel:</strong> {store_info['Channel']}</p>
                    </div>

                    <h4>Models with Decreased Displays</h4>
                    <table>
                        <thead>
                            <tr>
                                <th>Model</th>
                                <th style="text-align: center;">Previous</th>
                                <th style="text-align: center;">Current</th>
                                <th style="text-align: center;">Change</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
            """

        # Determine intro message based on store count
        store_count = len(stores_data)
        if store_count == 1:
            intro_msg = "This is an automated notification regarding display decreases detected at your store."
        else:
            intro_msg = f"This is an automated notification regarding display decreases detected at {store_count} of your stores."

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #ddd; }}
                .store-block {{ margin: 20px 0; }}
                .store-info {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #dc3545; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background-color: white; }}
                th {{ background-color: #6c757d; color: white; padding: 12px; text-align: left; }}
                .footer {{ text-align: center; padding: 15px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>⚠️ Display Decrease Alert</h2>
                    <p>Week {week_num} Report</p>
                </div>

                <div class="content">
                    <p>Dear {pic_name},</p>

                    <p>{intro_msg}</p>

                    {stores_html}

                    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                        <h4 style="margin-top: 0;">⚡ Action Required</h4>
                        <p>Please review the display decreases above and take appropriate action:</p>
                        <ul>
                            <li>Verify the accuracy of the display counts</li>
                            <li>Investigate reasons for any decreases</li>
                            <li>Plan corrective actions if needed</li>
                            <li>Update displays to maintain brand visibility</li>
                        </ul>
                    </div>

                    <p>If you have any questions or need support, please contact your regional manager.</p>

                    <p>Best regards,<br>
                    <strong>Display Tracking System</strong></p>
                </div>

                <div class="footer">
                    <p>This is an automated email from the Display Tracking System.</p>
                    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _generate_pic_email_text(self, pic_name: str, stores_data: List[Dict],
                                  week_num: int) -> str:
        """Generate plain text email content for PIC (supports multiple stores)"""

        # Determine intro message based on store count
        store_count = len(stores_data)
        if store_count == 1:
            intro_msg = "This is an automated notification regarding display decreases detected at your store."
        else:
            intro_msg = f"This is an automated notification regarding display decreases detected at {store_count} of your stores."

        text = f"""
Display Decrease Alert - Week {week_num}

Dear {pic_name},

{intro_msg}

"""

        # Add each store's information
        for idx, store_data in enumerate(stores_data):
            store_info = store_data['store_info']
            decreases = store_data['decreases']

            # Add separator between stores
            if idx > 0:
                text += "\n" + "="*70 + "\n\n"

            text += f"""STORE {idx + 1}: {store_info['Store_name']}
-----------------
Elux ID: {store_info['Elux_ID']}
Dealer ID: {store_info['Dealer_ID']}
Channel: {store_info['Channel']}

MODELS WITH DECREASED DISPLAYS
-------------------------------
"""

            for dec in decreases:
                text += f"""
Model: {dec['Model']}
  Previous: {int(dec['Previous'])}
  Current: {int(dec['Current'])}
  Change: {int(dec['Difference'])}
"""

        text += """

ACTION REQUIRED
---------------
Please review the display decreases above and take appropriate action:
- Verify the accuracy of the display counts
- Investigate reasons for any decreases
- Plan corrective actions if needed
- Update displays to maintain brand visibility

If you have any questions or need support, please contact your regional manager.

Best regards,
Display Tracking System

---
This is an automated email from the Display Tracking System.
Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return text

    def _generate_boss_email_html(self, summary_data: Dict, decreases_df: pd.DataFrame,
                                   week_num: int) -> str:
        """Generate HTML email content for boss summary"""

        # Get top stores with most decreases
        if not decreases_df.empty and 'Elux_ID' in decreases_df.columns:
            store_summary = decreases_df.groupby(['Elux_ID', 'Store_name']).agg({
                'Difference': 'sum'
            }).reset_index().sort_values('Difference').head(10)

            top_stores_html = ""
            for _, row in store_summary.iterrows():
                top_stores_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{row['Store_name']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{row['Elux_ID']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; color: #dc3545; font-weight: bold;">{int(row['Difference'])}</td>
                </tr>
                """
        else:
            top_stores_html = "<tr><td colspan='3' style='padding: 8px; text-align: center;'>No data available</td></tr>"

        total_decrease = int(decreases_df['Difference'].sum()) if not decreases_df.empty else 0
        affected_stores = len(decreases_df['Store_name'].unique()) if not decreases_df.empty and 'Store_name' in decreases_df.columns else 0
        affected_models = len(decreases_df['Model'].unique()) if not decreases_df.empty else 0

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #0056b3; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #ddd; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-card {{ background-color: white; padding: 15px; border-radius: 5px; text-align: center; flex: 1; margin: 0 10px; border: 1px solid #ddd; }}
                .stat-value {{ font-size: 28px; font-weight: bold; color: #dc3545; }}
                .stat-label {{ color: #666; font-size: 14px; margin-top: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background-color: white; }}
                th {{ background-color: #6c757d; color: white; padding: 10px; text-align: left; }}
                .footer {{ text-align: center; padding: 15px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📊 Weekly Display Decrease Summary</h2>
                    <p>Week {week_num} Report</p>
                </div>

                <div class="content">
                    <p>Dear Management,</p>

                    <p>This is your weekly summary of display decreases across all monitored stores.</p>

                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-value">{affected_stores}</div>
                            <div class="stat-label">Stores Affected</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{affected_models}</div>
                            <div class="stat-label">Models Decreased</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{total_decrease}</div>
                            <div class="stat-label">Total Decrease</div>
                        </div>
                    </div>

                    <h3>Top 10 Stores with Most Decreases</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Store Name</th>
                                <th>Elux ID</th>
                                <th style="text-align: center;">Total Decrease</th>
                            </tr>
                        </thead>
                        <tbody>
                            {top_stores_html}
                        </tbody>
                    </table>

                    <div style="background-color: #d1ecf1; border-left: 4px solid #0c5460; padding: 15px; margin: 20px 0;">
                        <h4 style="margin-top: 0;">📎 Attachments</h4>
                        <p>Please find the detailed decrease report attached to this email.</p>
                        <p>The attachment contains:</p>
                        <ul>
                            <li>Complete list of all decreases by model</li>
                            <li>Store-level breakdown</li>
                            <li>Previous and current display counts</li>
                        </ul>
                    </div>

                    <p>Individual store PICs have been notified of decreases at their respective locations.</p>

                    <p>Best regards,<br>
                    <strong>Display Tracking System</strong></p>
                </div>

                <div class="footer">
                    <p>This is an automated email from the Display Tracking System.</p>
                    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _generate_boss_email_text(self, summary_data: Dict, decreases_df: pd.DataFrame,
                                   week_num: int) -> str:
        """Generate plain text email content for boss summary"""

        total_decrease = int(decreases_df['Difference'].sum()) if not decreases_df.empty else 0
        affected_stores = len(decreases_df['Store_name'].unique()) if not decreases_df.empty and 'Store_name' in decreases_df.columns else 0
        affected_models = len(decreases_df['Model'].unique()) if not decreases_df.empty else 0

        text = f"""
Weekly Display Decrease Summary - Week {week_num}

Dear Management,

This is your weekly summary of display decreases across all monitored stores.

SUMMARY STATISTICS
------------------
Stores Affected: {affected_stores}
Models Decreased: {affected_models}
Total Decrease: {total_decrease}

TOP 10 STORES WITH MOST DECREASES
----------------------------------
"""

        if not decreases_df.empty and 'Elux_ID' in decreases_df.columns:
            store_summary = decreases_df.groupby(['Elux_ID', 'Store_name']).agg({
                'Difference': 'sum'
            }).reset_index().sort_values('Difference').head(10)

            for _, row in store_summary.iterrows():
                text += f"\n{row['Store_name']} (ID: {row['Elux_ID']}): {int(row['Difference'])}"

        text += """

ATTACHMENTS
-----------
Please find the detailed decrease report attached to this email.

The attachment contains:
- Complete list of all decreases by model
- Store-level breakdown
- Previous and current display counts

Individual store PICs have been notified of decreases at their respective locations.

Best regards,
Display Tracking System

---
This is an automated email from the Display Tracking System.
Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return text


# Utility function to load shop contacts
def load_shop_contacts(contacts_file='shop_contacts.csv', use_mongodb=True) -> pd.DataFrame:
    """
    Load shop PIC contacts from MongoDB or CSV file (fallback)

    Args:
        contacts_file: Path to contacts CSV file (fallback)
        use_mongodb: Whether to use MongoDB (default: True)

    Returns:
        DataFrame with contact information
    """
    try:
        # Try MongoDB first if enabled
        if use_mongodb:
            try:
                from db_manager import load_shop_contacts_from_db
                df = load_shop_contacts_from_db()
                if not df.empty:
                    logging.info(f"Loaded {len(df)} contacts from MongoDB")
                    return df
                else:
                    logging.warning("No contacts found in MongoDB, falling back to CSV")
            except ImportError:
                logging.warning("db_manager not available, falling back to CSV")
            except Exception as e:
                logging.warning(f"MongoDB connection failed: {e}, falling back to CSV")

        # Fallback to CSV file
        if os.path.exists(contacts_file):
            df = pd.read_csv(contacts_file, encoding='utf-8')
            # Validate required columns
            required_cols = ['Elux_ID', 'Dealer_ID', 'Store_name', 'PIC_Email']
            if all(col in df.columns for col in required_cols):
                logging.info(f"Loaded {len(df)} contacts from CSV")
                return df
            else:
                logging.error(f"Missing required columns in {contacts_file}")
                return pd.DataFrame()
        else:
            logging.warning(f"Contacts file not found: {contacts_file}")
            return pd.DataFrame()
    except Exception as e:
        logging.error(f"Error loading contacts: {e}")
        return pd.DataFrame()


# Example usage
if __name__ == "__main__":
    # Test email notifier
    notifier = EmailNotifier()

    if notifier.enabled:
        # Test sending
        test_email = input("Enter test email address: ")
        success = notifier.send_test_email(test_email)
        print(f"Test email sent: {success}")
    else:
        print("Email notifier not configured. Set GMAIL_EMAIL and GMAIL_APP_PASSWORD environment variables.")