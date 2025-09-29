
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import logging

class DisplayTracker:
    def __init__(self, log_file='display_tracker.log'):
        # Setup logging
        logging.basicConfig(
            filename=log_file, 
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

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

            # Fill NaN with 0
            for col in merged.columns[4:]:
                merged[col] = merged[col].fillna(0)

            # Identify model column pairs and compute new totals
            model_cols = []
            for col in merged.columns[4:]:
                if col.endswith('_old'):
                    base = col[:-4]
                    add_col = base + '_add'
                    if add_col in merged.columns:
                        model_cols.append((base, col, add_col))
                        merged[base] = merged[col] + merged[add_col]
                    else:
                        merged[add_col] = 0
                        model_cols.append((base, col, add_col))
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
                    prev_val = row[old_col]
                    curr_val = row[old_col] + row[add_col]  # Cumulative total
                    diff = curr_val - prev_val

                    if diff != 0:  # Only track changes
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
                'all_changes': changes_df.to_dict('records')
            }

            self.logger.info(f"Generated alerts: {len(changes)} total changes")
            return alert_summary

        except Exception as e:
            self.logger.error(f"Error generating alerts: {e}")
            raise

    def save_results(self, updated_report, alert_summary, week_num):
        """Save updated report and alert summary"""
        try:
            # Save updated report
            report_filename = f'report-week-{week_num}.csv'
            updated_report.to_csv(report_filename, index=False, encoding='utf-8')

            # Save alert summary
            alert_filename = f'alerts-week-{week_num}.json'
            with open(alert_filename, 'w', encoding='utf-8') as f:
                json.dump(alert_summary, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved results: {report_filename}, {alert_filename}")
            return report_filename, alert_filename

        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            raise

    def process_weekly_data(self, raw_file, previous_report_file, week_num):
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
            report_file, alert_file = self.save_results(updated_report, alert_summary, week_num)

            self.logger.info(f"Weekly processing completed successfully")

            return {
                'success': True,
                'updated_report_file': report_file,
                'alert_file': alert_file,
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
