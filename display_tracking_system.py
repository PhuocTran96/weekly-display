
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import logging
from email_notifier import EmailNotifier, load_shop_contacts

class DisplayTracker:
    def __init__(self, log_file='display_tracker.log', enable_email=False,
                 gmail_email=None, gmail_password=None):
        # Setup logging
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Initialize email notifier
        self.email_notifier = EmailNotifier(
            smtp_email=gmail_email,
            smtp_password=gmail_password,
            enabled=enable_email
        )
        self.enable_email = enable_email

    def load_report_data(self, report_file):
        """Load and clean previous week report data"""
        try:
            df = pd.read_csv(report_file, encoding='utf-8')
            # Clean data: convert '-' to 0 and make numeric
            for col in df.columns[4:]:
                df[col] = pd.to_numeric(df[col].replace(' -   ', 0))

            # Convert ID columns to string
            id_cols = ['Elux ID', 'Dealer ID', 'Channel', 'Store_name']
            for col in id_cols:
                df[col] = df[col].astype(str)

            self.logger.info(f"Loaded report data: {df.shape}")
            return df
        except Exception as e:
            self.logger.error(f"Error loading report data: {e}")
            raise

    def load_raw_data(self, raw_file):
        """Load and process raw display data"""
        try:
            df = pd.read_csv(raw_file, encoding='utf-8')
            df['Value'] = pd.to_numeric(df['Value'])

            # Convert ID columns to string
            id_cols = ['Elux ID', 'Dealer ID', 'Channel', 'Store_name']
            for col in id_cols:
                df[col] = df[col].astype(str)

            # Pivot to store-model format
            pivot_df = df.pivot_table(
                index=id_cols, 
                columns='Model', 
                values='Value', 
                aggfunc='sum', 
                fill_value=0
            ).reset_index()

            self.logger.info(f"Loaded and pivoted raw data: {pivot_df.shape}")
            return pivot_df
        except Exception as e:
            self.logger.error(f"Error loading raw data: {e}")
            raise

    def merge_and_update(self, report_df, raw_pivot_df):
        """Merge previous report with new raw data"""
        try:
            # Merge datasets
            id_cols = ['Elux ID', 'Dealer ID', 'Channel', 'Store_name']
            merged = report_df.merge(
                raw_pivot_df,
                on=id_cols,
                how='outer',
                suffixes=('_old', '_add')
            )

            # Fill NaN with 0 for old values (stores new to system)
            for col in merged.columns[4:]:
                if col.endswith('_old'):
                    merged[col] = merged[col].fillna(0)

            # Identify model column pairs and compute new totals
            # For binary tracking: If store appears in new data, use new value; otherwise keep old value
            model_cols = []
            for col in merged.columns[4:]:
                if col.endswith('_old'):
                    base = col[:-4]
                    add_col = base + '_add'
                    if add_col in merged.columns:
                        model_cols.append((base, col, add_col))
                        # Binary logic: If new data exists (not NaN), use it; otherwise keep old value
                        # Use where() to conditionally update: where NaN in add_col, keep old_col value
                        merged[base] = merged[add_col].where(merged[add_col].notna(), merged[col])
                    else:
                        merged[add_col] = 0
                        model_cols.append((base, col, add_col))
                        # If no new data column exists, keep old value
                        merged[base] = merged[col]

            # Create final updated report
            final_cols = id_cols + [base for base, _, _ in model_cols]
            updated_report = merged[final_cols]

            self.logger.info(f"Merged data successfully: {updated_report.shape}")
            return updated_report, model_cols, merged

        except Exception as e:
            self.logger.error(f"Error merging data: {e}")
            raise

    def generate_alerts(self, merged_df, model_cols):
        """Generate change alerts for models"""
        try:
            # Create long format for analysis
            changes = []
            id_cols = ['Elux ID', 'Dealer ID', 'Channel', 'Store_name']

            for base, old_col, add_col in model_cols:
                for idx, row in merged_df.iterrows():
                    prev_val = row[old_col]  # Last Week (LW)
                    new_val_raw = row[add_col]  # New Week (NW) - may be NaN if store not in new data

                    # If store didn't appear in new week data (NaN), skip - keep old value (no change)
                    if pd.isna(new_val_raw):
                        continue

                    curr_val = new_val_raw
                    diff = curr_val - prev_val

                    # Binary comparison logic:
                    # - Increase: NW=1, LW=0 (newly added display)
                    # - Decrease: NW=0, LW=1 (lost display, only if store appeared in new data)
                    # - No Change: NW=0, LW=0 OR NW=1, LW=1 (maintained)
                    # - Not in new data: Keep old value (no change recorded)

                    if diff != 0:  # Only track actual changes
                        changes.append({
                            'Elux_ID': row['Elux ID'],
                            'Dealer_ID': row['Dealer ID'],
                            'Channel': row['Channel'],
                            'Store_name': row['Store_name'],
                            'Model': base,
                            'Previous': prev_val,
                            'Current': curr_val,
                            'Difference': diff,
                            'Change_Type': 'Increase' if diff > 0 else 'Decrease'
                        })

            changes_df = pd.DataFrame(changes)

            # Generate model summary
            model_summary = changes_df.groupby('Model').agg({
                'Previous': 'sum',
                'Current': 'sum', 
                'Difference': 'sum'
            }).reset_index()

            # Split increases and decreases
            increases = model_summary[model_summary['Difference'] > 0].sort_values('Difference', ascending=False)
            decreases = model_summary[model_summary['Difference'] < 0].sort_values('Difference')

            alert_summary = {
                'timestamp': datetime.now().isoformat(),
                'total_models_tracked': len(model_summary),
                'models_increased': len(increases),
                'models_decreased': len(decreases),
                'models_unchanged': len(model_cols) - len(model_summary),
                'top_increases': increases.head(15).to_dict('records'),
                'top_decreases': decreases.head(10).to_dict('records'),
                'all_changes': changes_df.to_dict('records'),
                'increases_df': increases,  # Full increases DataFrame
                'decreases_df': decreases   # Full decreases DataFrame
            }

            self.logger.info(f"Generated alerts: {len(changes)} total changes")
            return alert_summary

        except Exception as e:
            self.logger.error(f"Error generating alerts: {e}")
            raise

    def send_email_notifications(self, alert_summary, week_num, decreases_csv_path=None,
                                  boss_emails=None, send_pic_emails=True, send_boss_emails=True):
        """
        Send email notifications for decreases

        Args:
            alert_summary: Alert summary dictionary with all changes
            week_num: Week number
            decreases_csv_path: Path to decreases CSV file for attachment
            boss_emails: List of boss email addresses
            send_pic_emails: Whether to send emails to PICs
            send_boss_emails: Whether to send email to boss
        """
        if not self.enable_email:
            self.logger.info("Email notifications disabled - skipping")
            return

        try:
            # Get all decreases
            changes_df = pd.DataFrame(alert_summary.get('all_changes', []))
            decreases_df = alert_summary.get('decreases_df', pd.DataFrame())

            if changes_df.empty or decreases_df.empty:
                self.logger.info("No decreases found - no emails to send")
                return

            # Load shop contacts
            contacts_df = load_shop_contacts()

            if contacts_df.empty:
                self.logger.warning("Shop contacts file not found or empty - skipping PIC emails")
            elif send_pic_emails:
                # Send emails to PICs - group by PIC email to consolidate multiple stores
                decrease_changes = changes_df[changes_df['Change_Type'] == 'Decrease']

                # First, map each store to its PIC
                pic_stores_map = {}  # {pic_email: {pic_name: str, stores: [...]}}

                # Group by store to get decreases per store
                stores = decrease_changes.groupby(['Elux_ID', 'Dealer_ID', 'Store_name', 'Channel'])

                for store_key, store_data in stores:
                    elux_id, dealer_id, store_name, channel = store_key

                    # Find PIC contact info
                    contact = contacts_df[
                        (contacts_df['Elux_ID'] == str(elux_id)) |
                        (contacts_df['Store_name'] == str(store_name))
                    ]

                    if not contact.empty:
                        pic_email = contact.iloc[0]['PIC_Email']
                        pic_name = contact.iloc[0].get('PIC_Name', 'Store Manager')

                        # Initialize PIC entry if not exists
                        if pic_email not in pic_stores_map:
                            pic_stores_map[pic_email] = {
                                'pic_name': pic_name,
                                'stores': []
                            }

                        # Add store data to this PIC
                        store_info = {
                            'Elux_ID': elux_id,
                            'Dealer_ID': dealer_id,
                            'Store_name': store_name,
                            'Channel': channel
                        }

                        pic_stores_map[pic_email]['stores'].append({
                            'store_info': store_info,
                            'decreases': store_data.to_dict('records')
                        })
                    else:
                        self.logger.warning(f"No contact found for store: {store_name} ({elux_id})")

                # Now send one email per PIC with all their stores
                for pic_email, pic_data in pic_stores_map.items():
                    self.email_notifier.send_decrease_alert_to_pic(
                        pic_email=pic_email,
                        pic_name=pic_data['pic_name'],
                        stores_data=pic_data['stores'],
                        week_num=week_num
                    )

            # Send summary email to boss
            if send_boss_emails and boss_emails:
                summary_data = {
                    'models_increased': alert_summary.get('models_increased', 0),
                    'models_decreased': alert_summary.get('models_decreased', 0),
                    'total_changes': len(alert_summary.get('all_changes', []))
                }

                # Use decrease_changes (store-level) instead of decreases_df (model-level)
                decrease_changes = changes_df[changes_df['Change_Type'] == 'Decrease']

                self.email_notifier.send_boss_summary(
                    boss_emails=boss_emails,
                    summary_data=summary_data,
                    decreases_df=decrease_changes,
                    week_num=week_num,
                    csv_attachment_path=decreases_csv_path
                )

            self.logger.info("Email notifications sent successfully")

        except Exception as e:
            self.logger.error(f"Error sending email notifications: {e}")
            # Don't raise - email failures shouldn't stop the process

    def save_results(self, updated_report, alert_summary, week_num):
        """Save updated report and alert summary"""
        try:
            # Save updated report
            report_filename = f'report-week-{week_num}.csv'
            updated_report.to_csv(report_filename, index=False, encoding='utf-8')

            # Save increases CSV
            increases_filename = f'increases-week-{week_num}.csv'
            if 'increases_df' in alert_summary and not alert_summary['increases_df'].empty:
                alert_summary['increases_df'].to_csv(increases_filename, index=False, encoding='utf-8')
                self.logger.info(f"Saved increases report: {increases_filename}")

            # Save decreases CSV with store-level breakdown
            decreases_filename = f'decreases-week-{week_num}.csv'
            if 'all_changes' in alert_summary:
                # Filter only decreases from all_changes to get store-level detail
                all_changes_df = pd.DataFrame(alert_summary['all_changes'])
                if not all_changes_df.empty:
                    decreases_detail = all_changes_df[all_changes_df['Change_Type'] == 'Decrease']
                    if not decreases_detail.empty:
                        decreases_detail.to_csv(decreases_filename, index=False, encoding='utf-8')
                        self.logger.info(f"Saved decreases report with store-level breakdown: {decreases_filename}")
                    else:
                        self.logger.info("No decreases to save")
                else:
                    self.logger.info("No changes data available")
            elif 'decreases_df' in alert_summary and not alert_summary['decreases_df'].empty:
                # Fallback to model-level summary if all_changes not available
                alert_summary['decreases_df'].to_csv(decreases_filename, index=False, encoding='utf-8')
                self.logger.info(f"Saved decreases report (model-level only): {decreases_filename}")

            # Save alert summary JSON (remove DataFrames before saving)
            alert_filename = f'alerts-week-{week_num}.json'
            alert_summary_json = {k: v for k, v in alert_summary.items() if k not in ['increases_df', 'decreases_df']}
            with open(alert_filename, 'w', encoding='utf-8') as f:
                json.dump(alert_summary_json, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved results: {report_filename}, {alert_filename}, {increases_filename}, {decreases_filename}")
            return report_filename, alert_filename, decreases_filename

        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            raise

    def process_weekly_data(self, raw_file, previous_report_file, week_num,
                           send_emails=False, boss_emails=None, send_pic_emails=True,
                           send_boss_emails=True):
        """Main processing function"""
        try:
            self.logger.info(f"Starting weekly processing for Week {week_num}")

            # Load data
            report_df = self.load_report_data(previous_report_file)
            raw_pivot_df = self.load_raw_data(raw_file)

            # Merge and update
            updated_report, model_cols, merged_df = self.merge_and_update(report_df, raw_pivot_df)

            # Generate alerts
            alert_summary = self.generate_alerts(merged_df, model_cols)

            # Save results
            report_file, alert_file, decreases_file = self.save_results(updated_report, alert_summary, week_num)

            # Send email notifications if enabled
            if send_emails:
                self.send_email_notifications(
                    alert_summary=alert_summary,
                    week_num=week_num,
                    decreases_csv_path=decreases_file,
                    boss_emails=boss_emails,
                    send_pic_emails=send_pic_emails,
                    send_boss_emails=send_boss_emails
                )

            self.logger.info(f"Weekly processing completed successfully")

            return {
                'success': True,
                'updated_report_file': report_file,
                'alert_file': alert_file,
                'decreases_file': decreases_file,
                'summary': {
                    'models_increased': alert_summary['models_increased'],
                    'models_decreased': alert_summary['models_decreased'],
                    'total_changes': len(alert_summary['all_changes'])
                }
            }

        except Exception as e:
            self.logger.error(f"Weekly processing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Example usage
if __name__ == "__main__":
    tracker = DisplayTracker()

    # Process the current data
    result = tracker.process_weekly_data(
        raw_file='raw-display-w39.csv',
        previous_report_file='report-week-38.csv',
        week_num=39
    )

    if result['success']:
        print("Processing completed successfully!")
        print(f"Models increased: {result['summary']['models_increased']}")
        print(f"Models decreased: {result['summary']['models_decreased']}")
        print(f"Total changes: {result['summary']['total_changes']}")
    else:
        print(f"Processing failed: {result['error']}")
